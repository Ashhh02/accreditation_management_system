"""Central notification service.

Every notification in the system — workflow events, chat messages, deadline
alerts, account changes and announcements — is created through here so that
(1) it is persisted to the database and (2) it is pushed live to the user's
WebSocket group when a channel layer is available. The broadcast is best-effort:
a missing/broken channel layer must never break the database write, which makes
HTTP polling a safe fallback.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification

logger = logging.getLogger(__name__)


def user_group(user_id):
    return f'notify_user_{user_id}'


def broadcast_to_user(user_id, payload):
    """Send `payload` to the user's notification WebSocket group, if any."""
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            user_group(user_id),
            {'type': 'notify.event', 'payload': payload},
        )
    except Exception:  # pragma: no cover - defensive; WS must never block DB writes
        logger.warning('Failed to broadcast notification to user %s', user_id, exc_info=True)


def create_notification(user, kind, title, message, submission=None,
                        entity_type='', entity_id='', target_url='', broadcast=True):
    """Persist a notification and push it to the recipient's group."""
    notification = Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        message=message,
        submission=submission,
        entity_type=entity_type,
        entity_id=entity_id,
        target_url=target_url,
    )
    if broadcast:
        broadcast_to_user(user.id, {
            'kind': kind,
            'title': title,
            'message': message,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'target_url': target_url,
            'submission_id': submission.id if submission else None,
            'id': notification.id,
            'unread': True,
        })
    return notification


def notification_payload(notification):
    """Map a persisted Notification to the wire format shared by HTTP and WS."""
    return {
        'id': notification.id,
        'kind': notification.kind,
        'title': notification.title,
        'message': notification.message,
        'is_read': notification.is_read,
        'entity_type': notification.entity_type,
        'entity_id': notification.entity_id,
        'target_url': notification.target_url,
        'submission_id': notification.submission_id,
        'created_at': notification.created_at.isoformat(),
    }