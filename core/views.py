from django.views.generic import TemplateView


class NotificationsView(TemplateView):
    template_name = 'core/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = [
            {
                'title': 'Revision Requested',
                'message': 'Dr. A. Villanueva requested revisions for Area II faculty evidence under the College of Engineering.',
                'time_label': '10 min ago',
                'icon': 'alert',
                'tone': 'rose',
                'unread': True,
            },
            {
                'title': 'Evidence Submitted',
                'message': 'Prof. J. Reyes submitted supporting documents for Area III instruction.',
                'time_label': '1 hour ago',
                'icon': 'file',
                'tone': 'blue',
                'unread': True,
            },
            {
                'title': 'AI Recommendation',
                'message': 'The system flagged Area VIII with a readiness gap and recommends early follow-up before the deadline window narrows.',
                'time_label': '2 hours ago',
                'icon': 'bolt',
                'tone': 'maroon',
                'unread': True,
            },
            {
                'title': 'Deadline Reminder',
                'message': 'Level I preliminary submission for Student Services is due in 11 days and still needs two pending attachments.',
                'time_label': '4 hours ago',
                'icon': 'clock',
                'tone': 'gold',
                'unread': True,
            },
            {
                'title': 'User Approved',
                'message': 'Prof. Ana Gomez has been approved and can now access the accreditation workspace.',
                'time_label': 'yesterday',
                'icon': 'users',
                'tone': 'green',
                'unread': False,
            },
            {
                'title': 'Overdue Alert',
                'message': 'Area VII Student Services now has three overdue submissions past the internal review target.',
                'time_label': 'yesterday',
                'icon': 'alert',
                'tone': 'rose',
                'unread': False,
            },
            {
                'title': 'Report Generated',
                'message': 'The monthly compliance summary for July 2026 is ready for review and export.',
                'time_label': 'July 13',
                'icon': 'clipboard',
                'tone': 'slate',
                'unread': False,
            },
        ]

        unread_total = sum(1 for item in notifications if item['unread'])
        context.update(
            {
                'page_title': 'Notifications',
                'notifications': notifications,
                'unread_total': unread_total,
                'total_notifications': len(notifications),
            }
        )
        return context
