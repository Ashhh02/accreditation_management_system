from django.views.generic import TemplateView


class UserManagementView(TemplateView):
    template_name = 'accounts/user_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = [
            {
                'initials': 'JR',
                'name': 'Prof. Juan Reyes',
                'email': 'j.reyes@jmcfi.edu.ph',
                'role': 'Program Head',
                'role_tone': 'blue',
                'department': 'College of Engineering',
                'auth': 'Email',
                'status': 'Active',
                'status_tone': 'green',
                'approval': 'Approved',
                'approval_tone': 'green',
            },
            {
                'initials': 'EC',
                'name': 'Dr. Elena Cruz',
                'email': 'e.cruz@jmcfi.edu.ph',
                'role': 'Dean',
                'role_tone': 'rose',
                'department': 'College of Business',
                'auth': 'Google',
                'status': 'Active',
                'status_tone': 'green',
                'approval': 'Approved',
                'approval_tone': 'green',
            },
            {
                'initials': 'FS',
                'name': 'Ms. Flora Santos',
                'email': 'f.santos@jmcfi.edu.ph',
                'role': 'Area Chair',
                'role_tone': 'gold',
                'department': 'Student Affairs',
                'auth': 'Email',
                'status': 'Active',
                'status_tone': 'green',
                'approval': 'Approved',
                'approval_tone': 'green',
            },
            {
                'initials': 'RB',
                'name': 'Engr. Ramon Bautista',
                'email': 'r.bautista@jmcfi.edu.ph',
                'role': 'Program Head',
                'role_tone': 'blue',
                'department': 'College of Engineering',
                'auth': 'Email',
                'status': 'Pending',
                'status_tone': 'gold',
                'approval': 'Pending',
                'approval_tone': 'gold',
            },
            {
                'initials': 'LT',
                'name': 'Prof. Lea Torres',
                'email': 'l.torres@jmcfi.edu.ph',
                'role': 'Program Head',
                'role_tone': 'blue',
                'department': 'College of Education',
                'auth': 'Google',
                'status': 'Pending',
                'status_tone': 'gold',
                'approval': 'Pending',
                'approval_tone': 'gold',
            },
            {
                'initials': 'CB',
                'name': 'Dr. Carlos Bautista',
                'email': 'c.bautista@jmcfi.edu.ph',
                'role': 'External Accreditor',
                'role_tone': 'slate',
                'department': 'External',
                'auth': 'Email',
                'status': 'Active',
                'status_tone': 'green',
                'approval': 'Approved',
                'approval_tone': 'green',
            },
            {
                'initials': 'AD',
                'name': 'Ms. Alice Dela Cruz',
                'email': 'a.delacruz@jmcfi.edu.ph',
                'role': 'QA',
                'role_tone': 'green',
                'department': 'QA Office',
                'auth': 'Email',
                'status': 'Inactive',
                'status_tone': 'slate',
                'approval': 'Approved',
                'approval_tone': 'green',
            },
        ]
        context.update(
            {
                'page_title': 'User Management',
                'users': users,
                'user_stats': [
                    {'label': 'Total Users', 'value': 7, 'tone': 'rose'},
                    {'label': 'Active', 'value': 4, 'tone': 'green'},
                    {'label': 'Pending Approval', 'value': 2, 'tone': 'gold'},
                    {'label': 'Inactive', 'value': 1, 'tone': 'slate'},
                ],
            }
        )
        return context


class SettingsProfileView(TemplateView):
    template_name = 'accounts/settings_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'page_title': 'Settings & Profile',
                'settings_tabs': [
                    {'key': 'profile', 'label': 'Profile', 'icon': 'users', 'active': True},
                    {'key': 'password', 'label': 'Password', 'icon': 'settings', 'active': False},
                    {'key': 'notifications', 'label': 'Notifications', 'icon': 'bell', 'active': False},
                    {'key': 'assistant', 'label': 'Assistant', 'icon': 'sparkle', 'active': False},
                ],
                'profile': {
                    'initials': 'MS',
                    'name': 'Dr. Maria Santos',
                    'office': 'Quality Assurance Office',
                    'email': 'm.santos@jmcfi.edu.ph',
                    'role': 'QA Administrator',
                    'assignment': 'Assigned by Superadmin · Permanent',
                },
            }
        )
        return context
