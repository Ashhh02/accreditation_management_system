from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('notifications/feed/', views.NotificationFeedView.as_view(), name='notification_feed'),
    path('announcements/', views.AnnouncementsListView.as_view(), name='announcements'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('audit-history/', views.AuditHistoryView.as_view(), name='audit_history'),
]
