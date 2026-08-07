from django.urls import path

from . import views

app_name = 'accreditation'

urlpatterns = [
    path('levels-areas/', views.LevelsAreasView.as_view(), name='levels_areas'),
    path('submission-workspace/', views.SubmissionWorkspaceView.as_view(), name='submission_workspace'),
    path('submission-workspace/<slug:area_key>/', views.SubmissionWorkspaceView.as_view(), name='submission_workspace_area'),
    path('review-workflow/', views.ReviewWorkflowView.as_view(), name='review_workflow'),
]
