import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .notifications import user_group

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Live notification stream for a single authenticated user.

    The client connects to ``/ws/notifications/`` and immediately receives
    ``notify.event`` messages pushed through its ``notify_user_<pk>`` group.
    """

    async def connect(self):
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user_id = user.id
        await self.channel_layer.group_add(user_group(self.user_id), self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'message': 'Notifications live'})

    async def disconnect(self, close_code):
        if hasattr(self, 'user_id'):
            await self.channel_layer.group_discard(user_group(self.user_id), self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get('type')
        if action == 'ping':
            await self.send_json({'type': 'pong', 'at': content.get('at')})

    async def notify_event(self, event):
        await self.send_json({'type': 'notify', 'payload': event['payload']})