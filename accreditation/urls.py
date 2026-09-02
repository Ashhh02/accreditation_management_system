from django.urls import path

from . import db_views as views

app_name = 'accreditation'

urlpatterns = [
    path('levels-areas/', views.LevelsAreasView.as_view(), name='levels_areas'),
    path('area-details/<slug:area_key>/', views.AreaDetailsView.as_view(), name='area_details'),
    path('submission-workspace/', views.SubmissionWorkspaceView.as_view(), name='submission_workspace'),
    path('submission-workspace/<slug:area_key>/<slug:subarea_key>/', views.SubmissionWorkspaceView.as_view(), name='submission_workspace_subarea'),
    path('submission-workspace/<slug:area_key>/', views.SubmissionWorkspaceView.as_view(), name='submission_workspace_area'),
    path('evidence/<int:submission_id>/', views.EvidenceDetailView.as_view(), name='evidence_detail'),
    path('evidence-file/<int:file_id>/download/', views.EvidenceFileDownloadView.as_view(), name='evidence_file_download'),
    path('review/<int:submission_id>/', views.EvidenceReviewView.as_view(), name='evidence_review'),
    path('review-workflow/', views.ReviewWorkflowView.as_view(), name='review_workflow'),
]
