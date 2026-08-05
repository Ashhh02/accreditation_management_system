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
    extra_context = {'page_title': 'Submission Workspace'}


class ReviewWorkflowView(TemplateView):
    template_name = 'accreditation/review_workflow.html'
    extra_context = {'page_title': 'Review Workflow'}
