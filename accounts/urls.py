from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('select-role/', views.SelectRoleView.as_view(), name='select_role'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('settings/', views.SettingsProfileView.as_view(), name='settings_profile'),
]
