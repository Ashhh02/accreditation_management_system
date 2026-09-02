from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accreditation.models import (
    AccreditationArea,
    AccreditationCycle,
    AccreditationLevel,
    AccreditationSubArea,
    EvidenceRequirement,
)
from core.models import Department, Role, RoleAssignment, UserProfile


class CompanionAndReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        cls.department = Department.objects.create(code='ENG', name='College of Engineering', kind=Department.PROGRAM)
        cls.user = cls.make_user('intel-owner')
        cycle = AccreditationCycle.objects.create(
            name='Test Cycle', academic_year='2025-2026', status=AccreditationCycle.ACTIVE, is_active=True,
        )
        level = AccreditationLevel.objects.create(cycle=cycle, code='I', name='Level I')
        area = AccreditationArea.objects.create(level=level, code='Area I', name='Mission', slug='area-i')
        subarea = AccreditationSubArea.objects.create(area=area, code='1.1', title='Mission')
        cls.req = EvidenceRequirement.objects.create(
            area=area, subarea=subarea, code='1.1.1', title='Mission doc', required_description='Provide it.',
        )

    @classmethod
    def make_user(cls, username):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        profile = UserProfile.objects.create(user=user, department=cls.department, approval_status=UserProfile.APPROVED)
        assignment = RoleAssignment.objects.create(
            user=user, role=cls.role, department=cls.department, is_approved=True,
        )
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment'])
        return user

    def test_report_page_lists_kpis_and_risk(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('intelligence:reports_monitoring'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Overall Readiness')
        self.assertContains(response, 'Total Submissions')

    def test_report_export_requires_post_and_returns_text(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('intelligence:export_report'))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse('intelligence:export_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="accreditation-report.txt"')
        self.assertIn('Accreditation', response.content.decode())

    def test_companion_ask_returns_grounded_answer(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('intelligence:companion_ask'), {'question': 'Which evidence is missing?'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('answer', payload)
        self.assertTrue(payload['answer'].strip())

    def test_companion_ask_rejects_empty_question(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('intelligence:companion_ask'), {'question': '   '})
        self.assertEqual(response.status_code, 400)

    def test_ai_insights_page_lists_real_signals_and_ava_assessment(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('intelligence:ai_insights'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AVA')
        self.assertContains(response, 'Overall Readiness')
        self.assertContains(response, 'Document Versioning')
        self.assertContains(response, 'advisory')

    def test_companion_and_reports_require_approval(self):
        response = self.client.get(reverse('intelligence:smart_companion'))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('intelligence:ai_insights'))
        self.assertEqual(response.status_code, 302)
