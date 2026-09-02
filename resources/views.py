from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accreditation.db_views import status_label, status_tone
from accreditation.models import EvidenceFile, EvidenceSubmission
from core.access import accessible_repository_submissions
from core.mixins import ApprovedUserRequiredMixin

from .models import Conversation, Message, MessageRead
from .services import RateLimitedError, mark_read, message_serialize, post_message, unread_count


def _display_name(user):
    return user.get_full_name().strip() or user.username


def _initials(user):
    name = user.get_full_name().strip() or user.username
    parts = name.split()
    return ''.join(part[0] for part in parts[:2]).upper() or 'U'


def _time_label(moment):
    local = timezone.localtime(moment)
    if local.date() == timezone.localdate():
        return local.strftime('%I:%M %p').lstrip('0')
    return local.strftime('%b %d, %I:%M %p').replace(' 0', ' ')


class DocumentRepositoryView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'resources/document_repository.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = accessible_repository_submissions(self.request.user)
        evidence_files = EvidenceFile.objects.filter(
            version__submission__in=submissions,
            version__is_current=True,
        ).select_related(
            'version__submission__requirement__area__level',
            'version__submission__requirement__subarea',
            'version__submission__department',
            'version__submission__program_head',
        )
        documents = []
        for evidence_file in evidence_files:
            submission = evidence_file.version.submission
            requirement = submission.requirement
            name = evidence_file.original_name or evidence_file.file.name or evidence_file.link_url
            documents.append({
                'name': name,
                'department': submission.department.name,
                'details': f'{requirement.area.code} · {requirement.area.level.name} · {_display_name(submission.program_head)}',
                'tags': [requirement.area.name, requirement.subarea.code if requirement.subarea else 'Evidence'],
                'version': f'v{evidence_file.version.version_number}',
                'updated': f'Updated {evidence_file.created_at:%b %d, %Y}',
                'status': status_label(submission.status),
                'tone': status_tone(submission.status),
                'icon_tone': 'rose',
                'download_url': reverse('accreditation:evidence_file_download', args=[evidence_file.pk]),
            })
        total = len(documents)
        completed = submissions.filter(status__in={EvidenceSubmission.COMPLIED, EvidenceSubmission.CLOSED}).count()
        pending = submissions.filter(status__in={EvidenceSubmission.NEEDS_REVISION, EvidenceSubmission.UNDER_DEAN_REVIEW, EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW, EvidenceSubmission.UNDER_QA_REVIEW}).count()
        context.update(
            {
                'page_title': 'Document Repository',
                'documents': documents,
                'repo_stats': [
                    {'label': 'Total Documents', 'value': total, 'tone': 'rose'},
                    {'label': 'Approved / Closed', 'value': completed, 'tone': 'green'},
                    {'label': 'Pending / Revision', 'value': pending, 'tone': 'gold'},
                ],
            }
        )
        return context


def _ensure_membership(user):
    """Return a conversation for the user, creating/joining the shared working
    group on first access so the chat is usable without admin setup."""

    conversation = Conversation.objects.filter(members=user).first()
    if conversation:
        return conversation

    user_model = get_user_model()
    conversation = Conversation.objects.filter(title='Accreditation Working Group').first()
    if conversation is None:
        conversation = Conversation.objects.create(
            title='Accreditation Working Group',
            context='Internal accreditation collaboration',
            is_group_thread=True,
        )
    member_ids = set(conversation.members.values_list('id', flat=True))
    member_ids.update(
        user_model.objects.filter(
            is_active=True,
            profile__approval_status='APPROVED',
            role_assignments__is_approved=True,
        ).values_list('id', flat=True)
    )
    conversation.members.set(user_model.objects.filter(id__in=list(member_ids)))
    return conversation


class CommunicationView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'resources/communication.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        conversation_id = self.request.GET.get('conversation')
        if conversation_id:
            active = get_object_or_404(Conversation, pk=conversation_id, members=user)
        else:
            active = _ensure_membership(user)

        conversation_rows = Conversation.objects.filter(members=user).prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('author').order_by('-created_at'),
                to_attr='latest_messages',
            ),
            'members',
            Prefetch('reads', queryset=MessageRead.objects.filter(user=user), to_attr='reader_marks'),
        )
        conversations = []
        member_ids = list(active.members.values_list('id', flat=True))
        for conversation in conversation_rows:
            prefetched = conversation.latest_messages
            last = prefetched[0] if prefetched else None
            mark = conversation.reader_marks[0] if conversation.reader_marks else None
            last_read_at = mark.last_read_at if mark else None
            peer = next((member for member in conversation.members.all() if member.pk != user.pk), None)
            unread = 0
            for message in prefetched:
                if message.author_id != user.pk and (last_read_at is None or message.created_at > last_read_at):
                    unread += 1
            conversations.append({
                'id': conversation.id,
                'initials': _initials(peer or user),
                'name': conversation.title,
                'context': conversation.context,
                'preview': last.body[:90] if last else 'No messages yet',
                'time': _time_label(last.created_at) if last else '—',
                'unread': unread,
                'active': conversation.pk == active.pk,
                'pinned': conversation.is_group_thread,
            })

        message_rows = [message_serialize(message, viewer=user) for message in active.messages.select_related('author')[:50]]

        context.update({
            'page_title': 'Communication',
            'conversations': conversations,
            'messages': message_rows,
            'active_conversation': {
                'id': active.pk,
                'name': active.title,
                'context': active.context,
                'linked': f'Linked: {active.related_submission.requirement.code} Submission' if active.related_submission_id else '',
                'member_ids': member_ids,
            },
            'messages_api_url': reverse('resources:messages_api'),
            'read_api_url': reverse('resources:messages_read'),
            'ws_path': '/ws/communication/',
        })
        return context


class MessagesApiView(ApprovedUserRequiredMixin, View):
    """GET/POST JSON feed used by the chat UI (HTTP fallback to WebSockets)."""

    def get(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            pk=request.GET.get('conversation'),
            members=request.user,
        )
        items = [message_serialize(message, viewer=request.user) for message in conversation.messages.select_related('author').order_by('-created_at')[:50]]
        return JsonResponse({
            'conversation': conversation.pk,
            'messages': list(reversed(items)),
            'unread': unread_count(request.user, conversation),
        })

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            pk=request.POST.get('conversation'),
            members=request.user,
        )
        body = (request.POST.get('body') or '').strip()
        if not body:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
        try:
            message = post_message(
                conversation,
                author=request.user,
                body=body,
                client_message_id=(request.POST.get('client_message_id') or '').strip(),
            )
        except RateLimitedError:
            return JsonResponse({'error': 'You are sending messages too quickly.'}, status=429)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        return JsonResponse(message_serialize(message, viewer=request.user))


class MarkConversationReadView(ApprovedUserRequiredMixin, View):
    """Mark a conversation as read and broadcast that to its members."""

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            pk=request.POST.get('conversation'),
            members=request.user,
        )
        mark_read(request.user, conversation)
        return JsonResponse({'ok': True, 'conversation': conversation.pk})
