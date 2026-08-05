from django.views.generic import TemplateView


class LevelsAreasView(TemplateView):
    template_name = 'accreditation/levels_areas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        levels = [
            {
                'name': 'Level I',
                'status': 'Candidate Status',
                'compiled': 7,
                'pending': 2,
                'revision': 2,
                'active': True,
            },
            {
                'name': 'Level II',
                'status': 'Accredited Status',
                'compiled': 9,
                'pending': 1,
                'revision': 0,
                'active': False,
            },
            {
                'name': 'Level III',
                'status': 'Accredited Status II',
                'compiled': 10,
                'pending': 1,
                'revision': 0,
                'active': False,
            },
            {
                'name': 'Level IV',
                'status': 'Accredited Status III',
                'compiled': 11,
                'pending': 0,
                'revision': 0,
                'active': False,
            },
        ]
        areas = [
            {
                'code': 'Area I',
                'name': 'Philosophy and Objectives',
                'progress': 92,
                'tone': 'green',
                'compiled': 3,
                'pending': 1,
                'revision': 0,
                'missing': 0,
            },
            {
                'code': 'Area II',
                'name': 'Faculty',
                'progress': 78,
                'tone': 'gold',
                'compiled': 5,
                'pending': 2,
                'revision': 1,
                'missing': 1,
            },
            {
                'code': 'Area III',
                'name': 'Instruction',
                'progress': 85,
                'tone': 'green',
                'compiled': 4,
                'pending': 1,
                'revision': 1,
                'missing': 0,
            },
            {
                'code': 'Area IV',
                'name': 'Laboratories',
                'progress': 60,
                'tone': 'gold',
                'compiled': 3,
                'pending': 3,
                'revision': 1,
                'missing': 2,
            },
            {
                'code': 'Area V',
                'name': 'Research',
                'progress': 72,
                'tone': 'gold',
                'compiled': 4,
                'pending': 2,
                'revision': 0,
                'missing': 1,
            },
            {
                'code': 'Area VI',
                'name': 'Library',
                'progress': 88,
                'tone': 'green',
                'compiled': 5,
                'pending': 0,
                'revision': 1,
                'missing': 0,
            },
        ]
        context.update(
            {
                'page_title': 'Levels & Areas',
                'levels': levels,
                'areas': areas,
                'active_level': levels[0],
                'overview': {
                    'compiled': 7,
                    'pending': 2,
                    'revision': 2,
                },
            }
        )
        return context


class SubmissionWorkspaceView(TemplateView):
    template_name = 'accreditation/submission_workspace.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sub_areas = [
            {
                'code': 'III-1',
                'title': 'III.1 Curriculum Design',
                'status': 'Completed',
                'tone': 'green',
                'active': True,
            },
            {
                'code': 'III-2',
                'title': 'III.2 Instructional Methods',
                'status': 'Pending',
                'tone': 'gold',
                'active': False,
            },
            {
                'code': 'III-3',
                'title': 'III.3 Assessment & Evaluation',
                'status': 'Needs Revision',
                'tone': 'rose',
                'active': False,
            },
            {
                'code': 'III-4',
                'title': 'III.4 Student Performance Monitoring',
                'status': 'Pending',
                'tone': 'gold',
                'active': False,
            },
            {
                'code': 'III-5',
                'title': 'III.5 Faculty-Student Interaction',
                'status': 'Missing',
                'tone': 'slate',
                'active': False,
            },
        ]
        documents = [
            {
                'name': 'Updated_Syllabi_2025-2026.pdf',
                'meta': '2.4 MB · v3 · Uploaded Jul 14',
                'version': 'v3',
            },
            {
                'name': 'Instructional_Methods_Manual.docx',
                'meta': '1.1 MB · v2 · Uploaded Jul 10',
                'version': 'v2',
            },
            {
                'name': 'Assessment_Framework.pdf',
                'meta': '3.7 MB · v1 · Uploaded Jul 5',
                'version': 'v1',
            },
        ]
        remarks = [
            {
                'author': 'Dr. A. Villanueva',
                'date': 'Jul 12, 2026',
                'message': 'Please provide updated syllabi for all subjects taught in AY 2025-2026. Current documents are from 2023.',
                'tone': 'rose',
            },
            {
                'author': 'Dr. M. Santos',
                'date': 'Jul 8, 2026',
                'message': 'Instructional methods documentation is comprehensive. Approved for this subarea.',
                'tone': 'green',
            },
        ]
        context.update(
            {
                'page_title': 'Submission Workspace',
                'sub_areas': sub_areas,
                'documents': documents,
                'remarks': remarks,
                'missing_requirements': [
                    'Updated AY 2025-26 syllabi for all courses',
                    'Faculty instructional portfolio samples',
                ],
            }
        )
        return context


class ReviewWorkflowView(TemplateView):
    template_name = 'accreditation/review_workflow.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = [
            {
                'evidence': 'Philosophy & Objectives Evidence',
                'code': 'LVL1-I-001',
                'department': 'College of Engineering',
                'area': 'Area I',
                'submitted_by': 'Prof. J. Reyes',
                'status': 'Pending Review',
                'tone': 'gold',
                'reviewer': 'Dr. A. Villanueva',
                'date': 'Jul 14, 2026',
            },
            {
                'evidence': 'Faculty Credentials - Teaching Load',
                'code': 'LVL1-II-003',
                'department': 'College of Business',
                'area': 'Area II',
                'submitted_by': 'Dr. P. Gomez',
                'status': 'Needs Revision',
                'tone': 'rose',
                'reviewer': 'Dr. M. Santos',
                'date': 'Jul 13, 2026',
            },
            {
                'evidence': 'Instructional Methods Manual',
                'code': 'LVL1-III-002',
                'department': 'College of Education',
                'area': 'Area III',
                'submitted_by': 'Prof. L. Torres',
                'status': 'Compiled',
                'tone': 'green',
                'reviewer': 'Dr. E. Cruz',
                'date': 'Jul 12, 2026',
            },
            {
                'evidence': 'Laboratory Facilities Assessment',
                'code': 'LVL1-IV-001',
                'department': 'College of Engineering',
                'area': 'Area IV',
                'submitted_by': 'Engr. R. Santos',
                'status': 'Pending Review',
                'tone': 'gold',
                'reviewer': 'Unassigned',
                'date': 'Jul 11, 2026',
            },
            {
                'evidence': 'Research Output Compilation',
                'code': 'LVL1-V-001',
                'department': 'College of Nursing',
                'area': 'Area V',
                'submitted_by': 'Dr. C. Bautista',
                'status': 'Compiled',
                'tone': 'green',
                'reviewer': 'Dr. A. Villanueva',
                'date': 'Jul 10, 2026',
            },
            {
                'evidence': 'Library Resources Inventory',
                'code': 'LVL1-VI-001',
                'department': 'College of Business',
                'area': 'Area VI',
                'submitted_by': 'Ms. F. Lim',
                'status': 'Needs Revision',
                'tone': 'rose',
                'reviewer': 'Dr. M. Santos',
                'date': 'Jul 9, 2026',
            },
        ]
        context.update(
            {
                'page_title': 'Review Workflow',
                'review_stats': [
                    {'label': 'Pending Review', 'value': 2, 'tone': 'gold'},
                    {'label': 'Needs Revision', 'value': 2, 'tone': 'rose'},
                    {'label': 'Compiled', 'value': 2, 'tone': 'green'},
                ],
                'submissions': submissions,
                'submission_count': len(submissions),
            }
        )
        return context
