from django.views.generic import TemplateView


class UserManagementView(TemplateView):
    template_name = 'accounts/user_management.html'
    extra_context = {'page_title': 'User Management'}


class SettingsProfileView(TemplateView):
    template_name = 'accounts/settings_profile.html'
    extra_context = {'page_title': 'Settings & Profile'}
