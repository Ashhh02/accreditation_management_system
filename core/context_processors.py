"""
Site-wide context: the sidebar navigation map and the signed-in user
summary shown in the topbar. Kept in one place so the sidebar template
never hardcodes a link — add a section/item here and it shows up
everywhere automatically.
"""

from .access import active_assignment, can_approve_accounts, is_admin_user
from .models import Notification


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

    admin_items = [
        {
            'label': 'Settings & Profile',
            'icon': 'settings',
            'url_name': 'accounts:settings_profile',
        },
    ]
    if can_approve_accounts(request.user):
        admin_items.insert(0, {
            'label': 'User Management',
            'icon': 'users',
            'url_name': 'accounts:user_management',
        })
        admin_items.insert(1, {
            'label': 'Audit History',
            'icon': 'clock',
            'url_name': 'core:audit_history',
        })
    nav_sections[-1]['items'] = admin_items

    if request.user.is_authenticated and not is_admin_user(request.user):
        assignment = active_assignment(request.user)
        role_code = assignment.role.code if assignment else ''
        if role_code == 'PROGRAM_HEAD':
            nav_sections[1]['items'] = [
                item for item in nav_sections[1]['items']
                if item['url_name'] != 'accreditation:review_workflow'
            ]
        elif role_code in {'DEAN', 'AREA_CHAIR', 'QA', 'ACCREDITATION_HEAD'}:
            nav_sections[1]['items'] = [
                item for item in nav_sections[1]['items']
                if item['url_name'] != 'accreditation:submission_workspace'
            ]

    current_user_summary = {
        'name': 'Guest',
        'role': 'Sign in required',
        'role_context': 'JMCFI AMS',
        'initials': 'GU',
        'photo_url': '',
    }
    notification_count = 0
    if request.user.is_authenticated:
        assignment = active_assignment(request.user)
        profile = getattr(request.user, 'profile', None)
        name = request.user.get_full_name().strip() or request.user.username
        initials = ''.join(part[0] for part in name.split()[:2]).upper() or 'U'
        current_user_summary = {
            'name': name,
            'role': assignment.role.name if assignment else 'Pending Approval',
            'role_context': assignment.department.name if assignment else 'Awaiting assignment',
            'initials': initials,
            'photo_url': profile.photo.url if profile and profile.photo else '',
        }
        notification_count = Notification.objects.filter(user=request.user, is_read=False).count()

    for section in nav_sections:
        for item in section['items']:
            if item.get('url_name') == 'core:notifications':
                item['badge'] = notification_count

    return {
        'nav_sections': nav_sections,
        'current_user_summary': current_user_summary,
        'notification_count': notification_count,
    }
