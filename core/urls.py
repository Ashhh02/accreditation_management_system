from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('audit-history/', views.AuditHistoryView.as_view(), name='audit_history'),
]
