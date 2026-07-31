from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('settings/', views.SettingsProfileView.as_view(), name='settings_profile'),
]
