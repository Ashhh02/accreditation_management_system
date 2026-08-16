"""
Site-wide context: the sidebar navigation map and the signed-in user
summary shown in the topbar. Kept in one place so the sidebar template
never hardcodes a link — add a section/item here and it shows up
everywhere automatically.
"""


def site_nav(request):
    nav_sections = [
        {
            'label': 'Overview',
            'items': [
                {
                    'label': 'Dashboard',
                    'icon': 'grid',
                    'url_name': 'dashboard:index',
                },
                {
                    'label': 'Notifications',
                    'icon': 'bell',
                    'url_name': 'core:notifications',
                    'badge': 7,
                },
            ],
        },
        {
            'label': 'Accreditation',
            'items': [
                {
                    'label': 'Levels & Areas',
                    'icon': 'layers',
                    'url_name': 'accreditation:levels_areas',
                },
                {
                    'label': 'Evidence Workspace',
                    'icon': 'folder',
                    'url_name': 'accreditation:submission_workspace',
                },
                {
                    'label': 'Review Workflow',
                    'icon': 'clipboard',
                    'url_name': 'accreditation:review_workflow',
                },
            ],
        },
        {
            'label': 'Resources',
            'items': [
                {
                    'label': 'Document Repository',
                    'icon': 'cloud',
                    'url_name': 'resources:document_repository',
                },
                {
                    'label': 'Communication',
                    'icon': 'message',
                    'url_name': 'resources:communication',
                },
            ],
        },
        {
            'label': 'Intelligence',
            'items': [
                {
                    'label': 'Reports & Monitoring',
                    'icon': 'chart',
                    'url_name': 'intelligence:reports_monitoring',
                },
                {
                    'label': 'Smart Companion',
                    'icon': 'sparkle',
                    'url_name': 'intelligence:smart_companion',
                },
            ],
        },
        {
            'label': 'Administration',
            'items': [
                {
                    'label': 'User Management',
                    'icon': 'users',
                    'url_name': 'accounts:user_management',
                },
                {
                    'label': 'Settings & Profile',
                    'icon': 'settings',
                    'url_name': 'accounts:settings_profile',
                },
            ],
        },
    ]

    current_user_summary = {
        'name': 'Dr. Maria Santos',
        'role': 'QA Administrator',
        'role_context': 'Quality Assurance Office',
        'initials': 'MS',
    }

    return {
        'nav_sections': nav_sections,
        'current_user_summary': current_user_summary,
        'notification_count': 7,
    }
