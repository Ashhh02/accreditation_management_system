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
                'workspace_key': 'area-i',
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
        area_key = kwargs.get('area_key', 'area-iii')
        workspaces = {
            'area-i': {
                'area_code': 'Area I',
                'area_name': 'Philosophy and Objectives',
                'department': 'College of Engineering',
                'program_head': 'Prof. Juan Reyes',
                'active_subarea': 'I.1 Institutional Philosophy and Objectives',
                'requirements_count': 4,
                'status': 'Pending',
                'tone': 'gold',
                'score': '4',
                'score_label': 'Very Satisfactory',
                'actual_situation': 'The program philosophy, institutional vision, mission, and objectives are communicated through the student handbook, program materials, and department planning documents. The department reviews alignment with institutional priorities during annual planning.',
                'instructions': [
                    {'title': 'Institutional Vision, Mission, and Goals', 'description': 'Upload the current board-approved VMG document and indicate its approval date.', 'status': 'Required', 'tone': 'rose'},
                    {'title': 'Program Philosophy and Objectives', 'description': 'Provide the program philosophy, objectives, and the latest curriculum or program handbook page.', 'status': 'Required', 'tone': 'rose'},
                    {'title': 'Alignment Matrix', 'description': 'Show how program objectives align with institutional goals, graduate attributes, and learning outcomes.', 'status': 'Required', 'tone': 'gold'},
                    {'title': 'Dissemination Evidence', 'description': 'Include screenshots, meeting minutes, handbook pages, or orientation materials showing stakeholder communication.', 'status': 'Required', 'tone': 'gold'},
                ],
                'sub_areas': [
                    {'code': 'I-1', 'title': 'I.1 Institutional Philosophy and Objectives', 'status': 'Pending', 'tone': 'gold', 'active': True},
                    {'code': 'I-2', 'title': 'I.2 Stakeholder Participation', 'status': 'Completed', 'tone': 'green', 'active': False},
                    {'code': 'I-3', 'title': 'I.3 Program Alignment', 'status': 'Needs Revision', 'tone': 'rose', 'active': False},
                    {'code': 'I-4', 'title': 'I.4 Dissemination and Review', 'status': 'Pending', 'tone': 'gold', 'active': False},
                ],
                'documents': [
                    {'name': 'Institutional_Vision_Mission_Goals.pdf', 'meta': '1.8 MB · v2 · Uploaded Jul 14', 'version': 'v2'},
                    {'name': 'Program_Objectives_Alignment_Matrix.xlsx', 'meta': '0.9 MB · v1 · Uploaded Jul 12', 'version': 'v1'},
                ],
                'remarks': [
                    {'author': 'Dr. A. Villanueva', 'date': 'Jul 13, 2026', 'message': 'Please add the current board approval page for the institutional vision, mission, and goals.', 'tone': 'rose'},
                    {'author': 'Dr. M. Santos', 'date': 'Jul 9, 2026', 'message': 'The program objectives are clearly stated. Add the alignment matrix for final review.', 'tone': 'green'},
                ],
                'missing_requirements': ['Board-approved VMG document with current approval date', 'Evidence that program objectives were communicated to stakeholders'],
            },
            'area-iii': {
                'area_code': 'Area III',
                'area_name': 'Instruction',
                'department': 'College of Engineering',
                'program_head': 'Prof. Juan Reyes',
                'active_subarea': 'III.1 Curriculum Design',
                'requirements_count': 4,
                'status': 'Completed',
                'tone': 'green',
                'score': '4',
                'score_label': 'Very Satisfactory',
                'actual_situation': "The department employs a variety of instructional methods including lecture-discussion, problem-based learning, and collaborative group activities. Faculty members are encouraged to use technology-enhanced instruction through the institution's LMS platform.",
                'instructions': [
                    {'title': 'Current Course Syllabi', 'description': 'Upload approved syllabi for all courses delivered during the current academic year.', 'status': 'Required', 'tone': 'rose'},
                    {'title': 'Instructional Methods Documentation', 'description': 'Provide course guides, teaching plans, or manuals that show delivery approaches.', 'status': 'Required', 'tone': 'gold'},
                ],
                'sub_areas': [
                    {'code': 'III-1', 'title': 'III.1 Curriculum Design', 'status': 'Completed', 'tone': 'green', 'active': True},
                    {'code': 'III-2', 'title': 'III.2 Instructional Methods', 'status': 'Pending', 'tone': 'gold', 'active': False},
                    {'code': 'III-3', 'title': 'III.3 Assessment & Evaluation', 'status': 'Needs Revision', 'tone': 'rose', 'active': False},
                    {'code': 'III-4', 'title': 'III.4 Student Performance Monitoring', 'status': 'Pending', 'tone': 'gold', 'active': False},
                    {'code': 'III-5', 'title': 'III.5 Faculty-Student Interaction', 'status': 'Missing', 'tone': 'slate', 'active': False},
                ],
                'documents': [
                    {'name': 'Updated_Syllabi_2025-2026.pdf', 'meta': '2.4 MB · v3 · Uploaded Jul 14', 'version': 'v3'},
                    {'name': 'Instructional_Methods_Manual.docx', 'meta': '1.1 MB · v2 · Uploaded Jul 10', 'version': 'v2'},
                    {'name': 'Assessment_Framework.pdf', 'meta': '3.7 MB · v1 · Uploaded Jul 5', 'version': 'v1'},
                ],
                'remarks': [
                    {'author': 'Dr. A. Villanueva', 'date': 'Jul 12, 2026', 'message': 'Please provide updated syllabi for all subjects taught in AY 2025-2026. Current documents are from 2023.', 'tone': 'rose'},
                    {'author': 'Dr. M. Santos', 'date': 'Jul 8, 2026', 'message': 'Instructional methods documentation is comprehensive. Approved for this subarea.', 'tone': 'green'},
                ],
                'missing_requirements': ['Updated AY 2025-26 syllabi for all courses', 'Faculty instructional portfolio samples'],
            },
        }
        workspace = workspaces.get(area_key, workspaces['area-iii'])
        context.update(
            {
                'page_title': 'Submission Workspace',
                'workspace': workspace,
                'sub_areas': workspace['sub_areas'],
                'documents': workspace['documents'],
                'remarks': workspace['remarks'],
                'missing_requirements': workspace['missing_requirements'],
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
