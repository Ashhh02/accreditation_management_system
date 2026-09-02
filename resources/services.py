"""Message service layer shared by the HTTP API and the WebSocket consumer.

All message traffic flows through :func:`post_message` and
:func:`mark_read` so the two transports behave identically: same validation,
same de-duplication, same persistence, same notifications and the same live
broadcast to the conversation group.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

from core.notifications import create_notification
from core.ratelimit import hit_rate_limit

from .models import Message, MessageRead

logger = logging.getLogger(__name__)


class RateLimitedError(ValueError):
    """Raised when the author exceeds the per-user message rate limit."""


def conversation_group(conversation_id):
    return f'chat_conversation_{conversation_id}'


def message_serialize(message, viewer=None):
    local = timezone.localtime(message.created_at)
    if local.date() == timezone.localdate():
        time_label = local.strftime('%I:%M %p').lstrip('0')
    else:
        time_label = local.strftime('%b %d, %I:%M %p').replace(' 0', ' ')
    author = message.author
    name = author.get_full_name().strip() or author.username
    initials = ''.join(part[0] for part in name.split()[:2]).upper() or 'U'
    return {
        'id': message.id,
        'client_message_id': message.client_message_id,
        'author_id': author.id,
        'author': name,
        'initials': initials,
        'text': message.body,
        'time': time_label,
        'created_at': message.created_at.isoformat(),
        'mine': viewer is not None and message.author_id == viewer.id,
    }


def broadcast_to_conversation(conversation_id, payload):
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            conversation_group(conversation_id),
            {'type': 'chat.message', 'payload': payload},
        )
    except Exception:  # pragma: no cover - defensive; WS must never block persistence
        logger.warning('Failed to broadcast chat event for conversation %s', conversation_id, exc_info=True)


def post_message(conversation, author, body, client_message_id=''):
    """Validate, de-duplicate, persist and broadcast a chat message.

    Returns a :class:`~resources.models.Message`. Duplicate submissions (same
    conversation + client_message_id) return the originally persisted message
    instead of creating a second row — the client retry after a reconnect is
    therefore safe.
    """
    body = (body or '').strip()
    if not body:
        raise ValueError('Message cannot be empty.')
    rate = getattr(settings, 'RATE_LIMIT_MESSAGES', {'limit': 60, 'window': 300})
    if hit_rate_limit(None, 'message', rate['limit'], rate['window'], identity=author.pk):
        raise RateLimitedError('You are sending messages too quickly.')
    if client_message_id:
        duplicate = Message.objects.filter(
            conversation=conversation,
            client_message_id=client_message_id,
        ).select_related('author').first()
        if duplicate:
            return duplicate

    message = Message.objects.create(
        conversation=conversation,
        author=author,
        body=body,
        client_message_id=client_message_id or '',
    )
    conversation.save(update_fields=['updated_at'])
    for member in conversation.members.exclude(pk=author.pk).filter(is_active=True):
        create_notification(
            member,
            kind='chat',
            title='New message',
            message=f'{author.get_full_name() or author.username}: {body[:120]}',
            entity_type='Conversation',
            entity_id=str(conversation.pk),
            target_url=f'/resources/communication/?conversation={conversation.pk}',
        )
    broadcast_to_conversation(conversation.pk, {
        'conversation_id': conversation.pk,
        'event': 'message',
        'message': message_serialize(message),
    })
    return message


def mark_read(user, conversation):
    read, _ = MessageRead.objects.update_or_create(
        user=user,
        conversation=conversation,
        defaults={'last_read_at': timezone.now()},
    )
    broadcast_to_conversation(conversation.pk, {
        'conversation_id': conversation.pk,
        'event': 'read',
        'user_id': user.id,
        'user_name': user.get_full_name() or user.username,
        'at': read.last_read_at.isoformat(),
    })
    return read


def unread_count(user, conversation):
    last_read = MessageRead.objects.filter(user=user, conversation=conversation).values_list('last_read_at', flat=True).first()
    messages = conversation.messages.exclude(author=user)
    if last_read:
        messages = messages.filter(created_at__gt=last_read)
    return messages.count()
