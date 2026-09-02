import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation
from .services import conversation_group, mark_read, post_message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Live chat for conversation members.

    On connect the consumer joins the group for every conversation the user
    belongs to, so the server (not the client) decides which groups may be
    joined. Messages are persisted through the shared service layer and echoed
    to the group.
    """

    async def connect(self):
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user = user
        conversation_ids = await self._member_conversation_ids()
        self.conversation_ids = conversation_ids
        for conversation_id in conversation_ids:
            await self.channel_layer.group_add(conversation_group(conversation_id), self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'conversations': conversation_ids})

    async def disconnect(self, close_code):
        if hasattr(self, 'conversation_ids'):
            for conversation_id in self.conversation_ids:
                await self.channel_layer.group_discard(conversation_group(conversation_id), self.channel_name)

    @database_sync_to_async
    def _member_conversation_ids(self):
        return list(Conversation.objects.filter(members=self.user).values_list('id', flat=True))

    @database_sync_to_async
    def _member_conversation(self, conversation_id):
        return Conversation.objects.filter(pk=conversation_id, members=self.user).first()

    async def receive_json(self, content, **kwargs):
        action = content.get('type')
        if action == 'ping':
            await self.send_json({'type': 'pong', 'at': content.get('at')})
            return
        conversation_id = content.get('conversation_id') or content.get('conversation')
        conversation = await self._member_conversation(conversation_id) if conversation_id else None
        if conversation is None:
            await self.send_json({'type': 'error', 'error': 'Conversation not found.'})
            return

        if action == 'send_message':
            try:
                message = await self._post(conversation, content.get('body', ''), content.get('client_message_id', ''))
            except ValueError as exc:
                await self.send_json({'type': 'error', 'error': str(exc)})
                return
            if not message:
                return
        elif action == 'read':
            await self._mark_read(conversation)
        else:
            await self.send_json({'type': 'error', 'error': 'Unknown action.'})

    @database_sync_to_async
    def _post(self, conversation, body, client_message_id):
        return post_message(conversation, self.user, body, client_message_id)

    @database_sync_to_async
    def _mark_read(self, conversation):
        return mark_read(self.user, conversation)

    async def chat_message(self, event):
        await self.send_json({'type': 'chat', 'conversation_id': event['payload'].get('conversation_id'), 'event': event['payload'].get('event'), 'payload': event['payload']})