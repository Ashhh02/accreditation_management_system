from django.views.generic import TemplateView


class NotificationsView(TemplateView):
    template_name = 'core/notifications.html'
    extra_context = {'page_title': 'Notifications'}
