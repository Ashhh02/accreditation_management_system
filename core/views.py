from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timesince import timesince
from django.views.generic import TemplateView

from .access import accessible_submissions, can_approve_accounts, is_admin_user
from .mixins import AccountApprovalMixin, ApprovedUserRequiredMixin
from .models import Announcement, AuditLog, Notification
from .notifications import create_notification


NOTIFICATION_PRESENTATION = {
    'revision': ('Revision Requested', 'alert', 'rose'),
    'submission': ('Evidence Submitted', 'file', 'blue'),
    'review': ('Review Update', 'check', 'green'),
    'task': ('Task Assigned', 'clipboard', 'blue'),
    'account': ('Account Update', 'users', 'green'),
    'deadline': ('Deadline Reminder', 'clock', 'gold'),
    'chat': ('New Message', 'message', 'blue'),
    'announcement': ('Announcement', 'bell', 'maroon'),
    'system': ('System Notice', 'bolt', 'maroon'),
}


class NotificationsView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'core/notifications.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'mark_all_read':
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            messages.success(request, 'All notifications marked as read.')
        else:
            Notification.objects.filter(user=request.user, pk=request.POST.get('notification_id')).update(is_read=True)
        return redirect('core:notifications')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        notifications = Notification.objects.filter(user=self.request.user).select_related('submission')
        for notification in notifications:
            fallback_title, icon, tone = NOTIFICATION_PRESENTATION.get(
                notification.kind,
                (notification.title, 'bell', 'slate'),
            )
            rows.append({
                'id': notification.id,
                'kind': notification.kind,
                'title': notification.title or fallback_title,
                'message': notification.message,
                'time_label': f'{timesince(notification.created_at)} ago',
                'icon': icon,
                'tone': tone,
                'unread': not notification.is_read,
                'entity_type': notification.entity_type,
                'entity_id': notification.entity_id,
                'target_url': notification.target_url,
                'submission_url': reverse('accreditation:evidence_detail', args=[notification.submission_id]) if notification.submission_id else '',
            })
        unread_total = sum(1 for item in rows if item['unread'])
        context.update({
            'page_title': 'Notifications',
            'notifications': rows,
            'unread_total': unread_total,
            'total_notifications': len(rows),
        })
        return context


class NotificationFeedView(ApprovedUserRequiredMixin, TemplateView):
    """Lightweight JSON feed polled by the topbar so the bell stays live
    without reloading the page. Runs the same scoping rules as the page view."""

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(user=request.user).select_related('submission')[:12]
        items = [{
            'id': n.id,
            'title': NOTIFICATION_PRESENTATION.get(n.kind, (n.title, 'bell', 'slate'))[0] or n.title,
            'message': n.message,
            'kind': n.kind,
            'unread': not n.is_read,
            'time_label': f'{timesince(n.created_at)} ago',
            'created_at': n.created_at.isoformat(),
            'entity_type': n.entity_type,
            'entity_id': n.entity_id,
            'target_url': n.target_url,
            'submission_url': reverse('accreditation:evidence_detail', args=[n.submission_id]) if n.submission_id else '',
        } for n in notifications]
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread': unread, 'items': items})


class AuditHistoryView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'core/audit_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if is_admin_user(self.request.user) or can_approve_accounts(self.request.user):
            events = AuditLog.objects.all()
        else:
            events = AuditLog.objects.filter(submission__in=accessible_submissions(self.request.user))
        context.update({
            'page_title': 'Audit History',
            'events': events.select_related('actor', 'submission__requirement', 'submission__department')[:200],
        })
        return context


class AnnouncementsListView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'core/announcements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Announcements',
            'announcements': Announcement.objects.select_related('created_by'),
            'can_post': can_approve_accounts(self.request.user),
        })
        return context


class AnnouncementCreateView(AccountApprovalMixin, TemplateView):
    template_name = 'core/announcement_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Post Announcement'
        return context

    def post(self, request, *args, **kwargs):
        title = (request.POST.get('title') or '').strip()
        body = (request.POST.get('body') or '').strip()
        if not title or not body:
            messages.error(request, 'Title and message are required.')
            return redirect('core:announcement_create')
        announcement = Announcement.objects.create(title=title, body=body, created_by=request.user)

        recipients = get_user_model().objects.filter(
            is_active=True,
            profile__approval_status='APPROVED',
            role_assignments__is_approved=True,
        ).distinct()
        target_url = reverse('core:announcements')
        for user in recipients:
            if user.pk == request.user.pk:
                continue
            create_notification(
                user,
                kind='announcement',
                title=announcement.title,
                message=announcement.body[:180],
                entity_type='Announcement',
                entity_id=str(announcement.pk),
                target_url=target_url,
            )
        messages.success(request, 'Announcement posted and sent to all approved users.')
        return redirect('core:announcements')
