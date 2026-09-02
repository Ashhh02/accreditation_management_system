"""Create deadline notifications for approaching and overdue evidence
requirements in the active accreditation cycle.

Run on a schedule (e.g. a daily cron/systemd timer) or on demand:

    python manage.py notify_deadlines

Notifications are de-duplicated: an unread deadline notification for the same
requirement is not duplicated, so re-running the command is safe.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from accreditation.models import AccreditationCycle, EvidenceRequirement
from core.models import Notification
from core.notifications import create_notification

URGENT_DAYS = 7


class Command(BaseCommand):
    help = 'Notify approved users about approaching or overdue evidence deadlines.'

    def handle(self, *args, **options):
        cycle = AccreditationCycle.objects.filter(is_active=True).first()
        if cycle is None:
            self.stdout.write('No active accreditation cycle; nothing to do.')
            return

        today = timezone.localdate()
        horizon = today + timedelta(days=URGENT_DAYS)
        requirements = EvidenceRequirement.objects.filter(
            area__level__cycle=cycle,
            deadline__isnull=False,
            deadline__lte=horizon,
        ).select_related('area')

        users = get_user_model().objects.filter(
            is_active=True,
            profile__approval_status='APPROVED',
            role_assignments__is_approved=True,
        ).distinct()

        created = 0
        skipped = 0
        for requirement in requirements:
            days_left = (requirement.deadline - today).days
            if days_left >= 0:
                title = f'Deadline in {days_left} day(s)' if days_left else 'Deadline is today'
                message = f'{requirement.area.code} · {requirement.code}: {requirement.title} is due {requirement.deadline:%b %d, %Y}.'
            else:
                title = 'Deadline overdue'
                message = f'{requirement.area.code} · {requirement.code}: {requirement.title} was due {requirement.deadline:%b %d, %Y} ({abs(days_left)} day(s) ago).'
            target_url = reverse('accreditation:area_details', args=[requirement.area.slug])
            for user in users:
                already = Notification.objects.filter(
                    user=user,
                    kind='deadline',
                    entity_type='EvidenceRequirement',
                    entity_id=str(requirement.pk),
                    is_read=False,
                ).exists()
                if already:
                    skipped += 1
                    continue
                create_notification(
                    user,
                    kind='deadline',
                    title=title,
                    message=message,
                    entity_type='EvidenceRequirement',
                    entity_id=str(requirement.pk),
                    target_url=target_url,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Deadline notifications: {created} created, {skipped} already pending.'
        ))