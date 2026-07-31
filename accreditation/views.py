from django.views.generic import TemplateView


class LevelsAreasView(TemplateView):
    template_name = 'accreditation/levels_areas.html'
    extra_context = {'page_title': 'Levels & Areas'}


class SubmissionWorkspaceView(TemplateView):
    template_name = 'accreditation/submission_workspace.html'
    extra_context = {'page_title': 'Submission Workspace'}


class ReviewWorkflowView(TemplateView):
    template_name = 'accreditation/review_workflow.html'
    extra_context = {'page_title': 'Review Workflow'}
