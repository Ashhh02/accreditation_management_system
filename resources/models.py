from django.conf import settings
from django.db import models


class Conversation(models.Model):
    title = models.CharField(max_length=180)
    context = models.CharField(max_length=240, blank=True)
    is_group_thread = models.BooleanField(default=False)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    related_submission = models.ForeignKey(
        'accreditation.EvidenceSubmission',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return self.title


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='messages')
    body = models.TextField()
    client_message_id = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('conversation', 'client_message_id'),
                name='unique_conversation_client_message',
                condition=models.Q(client_message_id__gt=''),
            ),
        ]

    def __str__(self):
        return f'{self.author} · {self.body[:40]}'


class MessageRead(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_reads')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='reads')
    last_read_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-last_read_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'conversation'),
                name='unique_user_conversation_read',
            ),
        ]

    def __str__(self):
        return f'{self.user} has read {self.conversation}'
