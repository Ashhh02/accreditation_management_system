from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Department, Role, RoleAssignment, UserProfile

from .forms import EvidenceSubmissionForm
from .models import (
    AccreditationArea,
    AccreditationCycle,
    AccreditationLevel,
    AccreditationSubArea,
    EvidenceFile,
    EvidenceRequirement,
    EvidenceReview,
    EvidenceSubmission,
    EvidenceVersion,
)
from .workflow import approve_submission, request_revision, submit_submission


class AccreditationWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.roles = {
            code: Role.objects.create(code=code, name=name, sort_order=index)
            for index, (code, name) in enumerate((
                ('PROGRAM_HEAD', 'Program Head'),
                ('DEAN', 'Dean'),
                ('AREA_CHAIR', 'Area Chair'),
                ('QA', 'QA'),
            ))
        }
        cls.department = Department.objects.create(code='ENG', name='College of Engineering')
        cls.program = Department.objects.create(
            code='ENG-BSCIV',
            name='Bachelor of Science in Civil Engineering',
            kind=Department.PROGRAM,
            parent=cls.department,
        )
        cls.cycle = AccreditationCycle.objects.create(
            name='Test Cycle', academic_year='2025-2026', status=AccreditationCycle.ACTIVE, is_active=True,
        )
        cls.level = AccreditationLevel.objects.create(cycle=cls.cycle, code='I', name='Level I')
        cls.area = AccreditationArea.objects.create(level=cls.level, code='Area I', name='Philosophy and Objectives', slug='area-i')
        cls.subarea = AccreditationSubArea.objects.create(area=cls.area, code='1.1', title='Mission')
        cls.requirement = EvidenceRequirement.objects.create(
            area=cls.area,
            subarea=cls.subarea,
            code='1.1.1',
            title='Mission evidence',
            required_description='Provide the approved mission document.',
            deadline=timezone.localdate(),
        )
        cls.revision_requirement = EvidenceRequirement.objects.create(
            area=cls.area,
            subarea=cls.subarea,
            code='1.1.2',
            title='Vision evidence',
            required_description='Provide the approved vision document.',
        )
        cls.program_head = cls.make_user('program-head', 'Program Head', cls.roles['PROGRAM_HEAD'], cls.program)
        cls.dean = cls.make_user('dean', 'Dean', cls.roles['DEAN'], cls.department)
        cls.area_chair = cls.make_user('area-chair', 'Area Chair', cls.roles['AREA_CHAIR'], cls.department)
        cls.qa = cls.make_user('qa', 'QA', cls.roles['QA'], cls.department)
        cls.area_chair.role_assignment.assigned_areas.add(cls.area)

    @classmethod
    def make_user(cls, username, name, role, department):
        user = get_user_model().objects.create_user(username=username, password='secure-password')  # nosec B106 test fixture only
        user.first_name = name
        user.save(update_fields=['first_name'])
        profile = UserProfile.objects.create(
            user=user,
            department=department,
            approval_status=UserProfile.APPROVED,
        )
        assignment = RoleAssignment.objects.create(
            user=user,
            role=role,
            department=department,
            is_approved=True,
        )
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment', 'updated_at'])
        user.role_assignment = assignment
        return user

    def make_submission(self, requirement=None):
        return EvidenceSubmission.objects.create(
            requirement=requirement or self.requirement,
            department=self.program,
            program_head=self.program_head,
            created_by=self.program_head,
        )

    def test_submission_moves_through_all_internal_review_stages_and_closes(self):
        submission = self.make_submission()
        submit_submission(submission, self.program_head, 'meets', 'implemented', link_url='https://example.com/mission')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.UNDER_DEAN_REVIEW)
        self.assertEqual(submission.current_reviewer_id, self.dean.id)
        self.assertEqual(EvidenceVersion.objects.filter(submission=submission).count(), 1)

        approve_submission(submission, self.dean, 'Dean review complete.')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW)
        self.assertEqual(submission.current_reviewer_id, self.area_chair.id)

        approve_submission(submission, self.area_chair, 'Area review complete.')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.UNDER_QA_REVIEW)
        self.assertEqual(submission.current_reviewer_id, self.qa.id)

        approve_submission(submission, self.qa, 'Final internal review complete.')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.CLOSED)
        self.assertIsNotNone(submission.closed_at)
        self.assertEqual(EvidenceReview.objects.filter(submission=submission).count(), 4)
        self.assertTrue(EvidenceReview.objects.filter(submission=submission, decision=EvidenceReview.COMPLIED_DECISION).exists())
        self.assertTrue(EvidenceReview.objects.filter(submission=submission, decision=EvidenceReview.CLOSED_DECISION).exists())

    def test_revision_returns_to_same_reviewer_and_preserves_versions_and_remarks(self):
        submission = self.make_submission(self.revision_requirement)
        submit_submission(submission, self.program_head, 'first version', 'needs work', link_url='https://example.com/vision')
        request_revision(submission, self.dean, 'Please add the signed approval page.')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.NEEDS_REVISION)
        self.assertEqual(submission.current_reviewer_id, self.program_head.id)
        self.assertEqual(submission.revision_return_reviewer_id, self.dean.id)

        submit_submission(submission, self.program_head, 'revised version', 'updated and signed')
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.UNDER_DEAN_REVIEW)
        self.assertEqual(submission.current_reviewer_id, self.dean.id)
        self.assertEqual(EvidenceVersion.objects.filter(submission=submission).count(), 2)
        self.assertEqual(EvidenceReview.objects.filter(submission=submission).count(), 1)
        self.assertEqual(EvidenceReview.objects.get(submission=submission).remarks, 'Please add the signed approval page.')

    def test_reviewer_must_be_current_assignee(self):
        submission = self.make_submission()
        submit_submission(submission, self.program_head, 'meets', 'implemented', link_url='https://example.com/mission')
        with self.assertRaises(PermissionDenied):
            approve_submission(submission, self.area_chair, 'Wrong stage.')

    def test_program_head_cannot_manage_another_program_submission(self):
        other_program = Department.objects.create(
            code='BUS-BSBA', name='Bachelor of Science in Business Administration', kind=Department.PROGRAM,
        )
        other_user = self.make_user('other-head', 'Other', self.roles['PROGRAM_HEAD'], other_program)
        submission = self.make_submission()
        with self.assertRaises(PermissionDenied):
            submit_submission(submission, other_user, 'not allowed', 'not allowed')

    def test_evidence_pages_are_connected_to_database_records(self):
        self.client.force_login(self.program_head)
        self.assertEqual(self.client.get(reverse('accreditation:levels_areas')).status_code, 200)
        self.assertEqual(self.client.get(reverse('accreditation:area_details', args=[self.area.slug])).status_code, 200)
        response = self.client.get(reverse('accreditation:submission_workspace_subarea', args=[self.area.slug, '1-1']))
        self.assertEqual(response.status_code, 200)
        submission = EvidenceSubmission.objects.get(requirement=self.requirement, department=self.program)
        self.assertEqual(self.client.get(reverse('accreditation:evidence_detail', args=[submission.id])).status_code, 200)

    def test_my_tasks_landing_shows_assigned_and_missing_instead_of_subareas(self):
        self.client.force_login(self.program_head)

        response = self.client.get(reverse('accreditation:submission_workspace'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Tasks')
        self.assertContains(response, 'Assigned')
        self.assertContains(response, 'Missing')
        self.assertContains(response, 'Deadline:')
        self.assertNotContains(response, 'Sub-Areas')

    def test_versioning_supersedes_old_versions_and_marks_statuses(self):
        submission = self.make_submission()
        submit_submission(submission, self.program_head, 'v1 self', 'v1 actual', link_url='https://example.com/a', change_remarks='Initial upload')
        v1 = EvidenceVersion.objects.get(submission=submission, version_number=1)
        self.assertTrue(v1.is_current)
        self.assertEqual(v1.status, EvidenceVersion.SUBMITTED)
        self.assertEqual(v1.change_remarks, 'Initial upload')

        request_revision(submission, self.dean, 'Please add the signed approval page.')
        v1.refresh_from_db()
        self.assertEqual(v1.status, EvidenceVersion.NOT_APPROVED)

        submit_submission(submission, self.program_head, 'v2 self', 'v2 actual', link_url='https://example.com/b', change_remarks='Added signed page')
        v1.refresh_from_db()
        v2 = EvidenceVersion.objects.get(submission=submission, version_number=2)
        self.assertEqual(v1.status, EvidenceVersion.SUPERSEDED)
        self.assertFalse(v1.is_current)
        self.assertTrue(v2.is_current)
        self.assertEqual(v2.status, EvidenceVersion.SUBMITTED)

        approve_submission(submission, self.dean, 'Dean ok')
        approve_submission(submission, self.area_chair, 'Area ok')
        approve_submission(submission, self.qa, 'QA ok')
        v2.refresh_from_db()
        self.assertEqual(v2.status, EvidenceVersion.APPROVED)
        self.assertTrue(v2.is_current)
        self.assertEqual(submission.current_version.pk, v2.pk)

    def test_older_version_download_gated_for_reviewers_but_allowed_for_ph_and_qa(self):
        submission = self.make_submission()
        submit_submission(submission, self.program_head, 'v1 self', 'v1 actual', link_url='https://example.com/v1')
        request_revision(submission, self.dean, 'Please revise.')
        submit_submission(submission, self.program_head, 'v2 self', 'v2 actual', link_url='https://example.com/v2')
        old_file = EvidenceFile.objects.get(version__version_number=1)

        self.client.force_login(self.dean)
        response = self.client.get(reverse('accreditation:evidence_file_download', args=[old_file.id]))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.qa)
        response = self.client.get(reverse('accreditation:evidence_file_download', args=[old_file.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('example.com/v1', response.url)

        self.client.force_login(self.program_head)
        response = self.client.get(reverse('accreditation:evidence_file_download', args=[old_file.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('example.com/v1', response.url)

        current_file = EvidenceFile.objects.get(version__version_number=2)
        self.client.force_login(self.dean)
        response = self.client.get(reverse('accreditation:evidence_file_download', args=[current_file.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('example.com/v2', response.url)

    def test_workspace_submit_button_uses_the_workflow_service(self):
        submission = self.make_submission()
        submission.self_evaluation = 'Prepared self evaluation'
        submission.actual_situation = 'Prepared actual situation'
        submission.save(update_fields=['self_evaluation', 'actual_situation', 'last_updated'])
        version = EvidenceVersion.objects.create(
            submission=submission,
            version_number=1,
            self_evaluation=submission.self_evaluation,
            actual_situation=submission.actual_situation,
            submitted_by=self.program_head,
        )
        EvidenceFile.objects.create(version=version, uploaded_by=self.program_head, link_url='https://example.com/evidence', original_name='evidence link')
        self.client.force_login(self.program_head)
        response = self.client.post(
            reverse('accreditation:submission_workspace_subarea', args=[self.area.slug, '1-1']),
            {'action': 'submit'},
        )
        self.assertRedirects(response, reverse('accreditation:submission_workspace_subarea', args=[self.area.slug, '1-1']))
        submission.refresh_from_db()
        self.assertEqual(submission.status, EvidenceSubmission.UNDER_DEAN_REVIEW)

    def test_evidence_form_rejects_unsupported_file_types(self):
        submission = self.make_submission()
        html_file = SimpleUploadedFile('index.html', b'<script>alert(1)</script>', content_type='text/html')
        form = EvidenceSubmissionForm(
            {'self_evaluation': 'x', 'actual_situation': 'y'},
            {'files': [html_file]},
            instance=submission,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('files', form.errors)

    def test_evidence_form_rejects_mislabeled_executable_and_oversized_files(self):
        submission = self.make_submission()
        exe_file = SimpleUploadedFile(
            'evidence.pdf',
            b'MZ\x90\x00\x03\x00\x00\x00',
            content_type='application/x-msdownload',
        )
        form = EvidenceSubmissionForm(
            {'self_evaluation': 'x', 'actual_situation': 'y'},
            {'files': [exe_file]},
            instance=submission,
        )
        self.assertFalse(form.is_valid())

        big_file = SimpleUploadedFile('big.pdf', b'0' * (5 * 1024 * 1024 + 1), content_type='application/pdf')
        form = EvidenceSubmissionForm(
            {'self_evaluation': 'x', 'actual_situation': 'y'},
            {'files': [big_file]},
            instance=submission,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('files', form.errors)

    def test_evidence_form_accepts_allowed_document_files(self):
        submission = self.make_submission()
        for name, content_type in (
            ('evidence.pdf', 'application/pdf'),
            ('notes.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('photo.jpg', 'image/jpeg'),
            ('sheet.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        ):
            uploaded = SimpleUploadedFile(name, b'%s' % name.encode(), content_type=content_type)
            form = EvidenceSubmissionForm(
                {'self_evaluation': 'x', 'actual_situation': 'y'},
                {'files': [uploaded]},
                instance=submission,
            )
            self.assertTrue(form.is_valid(), form.errors)
