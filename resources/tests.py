from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

import asyncio

from channels.testing import WebsocketCommunicator

from config.asgi import application

from accreditation.models import (
    AccreditationArea,
    AccreditationCycle,
    AccreditationLevel,
    AccreditationSubArea,
    EvidenceFile,
    EvidenceRequirement,
    EvidenceSubmission,
    EvidenceVersion,
)
from core.access import accessible_repository_submissions
from core.models import Department, Role, RoleAssignment, UserProfile

from .models import Conversation, Message, MessageRead


_WS_LOOP = asyncio.new_event_loop()


def _run_ws(awaitable):
    """Run a coroutine on the single persistent WebSocket event loop.

    ``InMemoryChannelLayer`` schedules timers/futures on the loop active at
    call time; a fresh per-call loop (as ``async_to_sync`` creates) gets torn
    down while those timers are pending, cancelling the consumer. Sharing one
    loop for every WebSocket test keeps the layer and consumers lifecycle-stable.
    """
    return _WS_LOOP.run_until_complete(awaitable)


class DocumentRepositoryAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_head_role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        cls.admin_role = Role.objects.create(code='ADMIN', name='Admin')
        cls.qa_role = Role.objects.create(code='QA', name='QA')
        cls.engineering = Department.objects.create(
            code='ENG',
            name='College of Engineering',
            kind=Department.DEPARTMENT,
        )
        cls.civil = Department.objects.create(
            code='ENG-BSCIV',
            name='Bachelor of Science in Civil Engineering',
            kind=Department.PROGRAM,
            parent=cls.engineering,
        )
        cls.business = Department.objects.create(
            code='BUS',
            name='College of Business',
            kind=Department.DEPARTMENT,
        )
        cycle = AccreditationCycle.objects.create(
            name='Test Cycle',
            academic_year='2025-2026',
            status=AccreditationCycle.ACTIVE,
            is_active=True,
        )
        level = AccreditationLevel.objects.create(cycle=cycle, code='I', name='Level I')
        area = AccreditationArea.objects.create(
            level=level,
            code='Area I',
            name='Philosophy and Objectives',
            slug='area-i',
        )
        subarea = AccreditationSubArea.objects.create(area=area, code='1.1', title='Mission')
        cls.requirement = EvidenceRequirement.objects.create(
            area=area,
            subarea=subarea,
            code='1.1.1',
            title='Mission evidence',
            required_description='Provide the approved mission document.',
        )

        cls.uploader = cls.make_user(
            'uploader',
            cls.program_head_role,
            cls.civil,
        )
        cls.admin = cls.make_user('admin', cls.admin_role, cls.business)
        cls.qa = cls.make_user('qa', cls.qa_role, cls.business)

        cls.civil_submission = cls.make_submission(cls.civil, cls.uploader)
        cls.business_submission = cls.make_submission(cls.business, cls.uploader)
        for submission in (cls.civil_submission, cls.business_submission):
            version = EvidenceVersion.objects.create(
                submission=submission,
                version_number=1,
                submitted_by=cls.uploader,
            )
            EvidenceFile.objects.create(
                version=version,
                uploaded_by=cls.uploader,
                original_name=f'{submission.department.code} evidence.pdf',
            )

    @classmethod
    def make_user(cls, username, role, department):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        profile = UserProfile.objects.create(
            user=user,
            department=department,
            approval_status=UserProfile.APPROVED,
        )
        assignment = RoleAssignment.objects.create(
            user=user,
            role=role,
            department=department,
            is_approved=True,
        )
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment'])
        return user

    @classmethod
    def make_submission(cls, department, program_head):
        return EvidenceSubmission.objects.create(
            requirement=cls.requirement,
            department=department,
            program_head=program_head,
            created_by=program_head,
        )

    def test_program_head_sees_only_active_program_documents(self):
        submissions = accessible_repository_submissions(self.uploader)

        self.assertEqual(set(submissions), {self.civil_submission})

    def test_admin_and_qa_can_see_all_repository_documents(self):
        self.assertEqual(
            set(accessible_repository_submissions(self.admin)),
            {self.civil_submission, self.business_submission},
        )
        self.assertEqual(
            set(accessible_repository_submissions(self.qa)),
            {self.civil_submission, self.business_submission},
        )


class CommunicationAndMessagesApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        cls.department = Department.objects.create(code='TEST', name='Test Program', kind=Department.PROGRAM)
        cls.owner = cls.make_user('chat-owner')
        cls.peer = cls.make_user('chat-peer')

    @classmethod
    def make_user(cls, username):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        profile = UserProfile.objects.create(user=user, department=cls.department, approval_status=UserProfile.APPROVED)
        assignment = RoleAssignment.objects.create(user=user, role=cls.role, department=cls.department, is_approved=True)
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment'])
        return user

    def test_first_access_creates_and_joins_shared_group(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('resources:communication'))

        conversation = Conversation.objects.get(title='Accreditation Working Group')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(conversation.members.filter(pk=self.owner.pk).exists())
        self.assertTrue(conversation.members.filter(pk=self.peer.pk).exists())
        self.assertContains(response, conversation.title)

    def test_messages_api_posts_and_returns_message(self):
        self.client.force_login(self.owner)
        self.client.get(reverse('resources:communication'))
        conversation = Conversation.objects.get(title='Accreditation Working Group')

        response = self.client.post(
            reverse('resources:messages_api'),
            {'conversation': conversation.pk, 'body': 'Hello from Core'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Message.objects.filter(conversation=conversation, author=self.owner, body='Hello from Core').exists())
        payload = response.json()
        self.assertEqual(payload['text'], 'Hello from Core')
        self.assertTrue(payload['mine'])

    def test_messages_api_rejects_empty_body(self):
        self.client.force_login(self.owner)
        self.client.get(reverse('resources:communication'))
        conversation = Conversation.objects.get(title='Accreditation Working Group')

        response = self.client.post(
            reverse('resources:messages_api'),
            {'conversation': conversation.pk, 'body': '   '},
        )

        self.assertEqual(response.status_code, 400)

    def test_messages_api_requires_membership(self):
        outsider = self.make_user('chat-outsider')
        self.client.force_login(outsider)
        conversation = Conversation.objects.create(title='Private', context='private')

        response = self.client.get(reverse('resources:messages_api'), {'conversation': conversation.pk})

        self.assertEqual(response.status_code, 404)

    def test_messages_api_deduplicates_client_message_id(self):
        self.client.force_login(self.owner)
        self.client.get(reverse('resources:communication'))
        conversation = Conversation.objects.get(title='Accreditation Working Group')

        first = self.client.post(
            reverse('resources:messages_api'),
            {'conversation': conversation.pk, 'body': 'Idempotent', 'client_message_id': 'same'},
        )
        second = self.client.post(
            reverse('resources:messages_api'),
            {'conversation': conversation.pk, 'body': 'Idempotent', 'client_message_id': 'same'},
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            Message.objects.filter(conversation=conversation, client_message_id='same').count(),
            1,
        )
        self.assertEqual(first.json()['id'], second.json()['id'])

    @override_settings(RATE_LIMIT_MESSAGES={'limit': 3, 'window': 300})
    def test_messages_api_rate_limits_per_user(self):
        cache.clear()
        self.client.force_login(self.owner)
        self.client.get(reverse('resources:communication'))
        conversation = Conversation.objects.get(title='Accreditation Working Group')

        for count in range(1, 4):
            response = self.client.post(
                reverse('resources:messages_api'),
                {'conversation': conversation.pk, 'body': f'Message {count}', 'client_message_id': f'rl-{count}'},
            )
            self.assertEqual(response.status_code, 200, f'post {count} should be allowed')

        limited = self.client.post(
            reverse('resources:messages_api'),
            {'conversation': conversation.pk, 'body': 'Message 4'},
        )
        self.assertEqual(limited.status_code, 429)
        self.assertIn('too quickly', limited.json()['error'])

    def test_messages_api_get_lists_history_in_order(self):
        self.client.force_login(self.owner)
        self.client.get(reverse('resources:communication'))
        conversation = Conversation.objects.get(title='Accreditation Working Group')
        Message.objects.create(conversation=conversation, author=self.owner, body='one')
        Message.objects.create(conversation=conversation, author=self.peer, body='two')

        response = self.client.get(reverse('resources:messages_api'), {'conversation': conversation.pk})

        payload = response.json()
        bodies = [item['text'] for item in payload['messages']]
        self.assertEqual(bodies, ['one', 'two'])


class ChatWebSocketTests(TransactionTestCase):
    """End-to-end WebSocket tests running the real ASGI application.

    Uses ``TransactionTestCase`` because the consumer persists messages on a
    separate thread; a ``TestCase`` transaction would hide those writes from
    the test connection.
    """

    def setUp(self):
        role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        department = Department.objects.create(code='WSDEPT', name='WS Program', kind=Department.PROGRAM)
        self.alice = self.make_user('ws-alice', role, department)
        self.bob = self.make_user('ws-bob', role, department)
        self.conversation = Conversation.objects.create(title='WS Test')
        self.conversation.members.set([self.alice, self.bob])

    def make_user(self, username, role, department):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        UserProfile.objects.create(user=user, department=department, approval_status=UserProfile.APPROVED)
        RoleAssignment.objects.create(user=user, role=role, department=department, is_approved=True)
        return user

    def _communicator(self, user, origin=b'http://testserver'):
        from django.contrib.sessions.backends.db import SessionStore

        headers = [(b'origin', origin)]
        if user is not None:
            session = SessionStore()
            session['_auth_user_id'] = str(user.pk)
            session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
            session['_auth_user_hash'] = user.get_session_auth_hash()
            session.create()
            headers.append((b'cookie', f'sessionid={session.session_key}'.encode()))
        return WebsocketCommunicator(application, '/ws/communication/', headers=headers)

    async def _connect(self, communicator, user):
        connected, _ = await communicator.connect()
        if not connected:
            raise AssertionError(f'Connection rejected for {user.username}')
        await communicator.receive_json_from(timeout=2)
        return communicator

    def test_anonymous_connection_is_rejected(self):
        communicator = self._communicator(None)

        async def scenario():
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, 4401)

        _run_ws(scenario())

    def test_message_broadcasts_to_all_members(self):
        alice_c = self._communicator(self.alice)
        bob_c = self._communicator(self.bob)

        async def scenario():
            await self._connect(alice_c, self.alice)
            await self._connect(bob_c, self.bob)

            await alice_c.send_json_to({
                'type': 'send_message',
                'conversation_id': self.conversation.pk,
                'body': 'Hello via WS',
                'client_message_id': 'abc123',
            })

            alice_event = await alice_c.receive_json_from(timeout=2)
            bob_event = await bob_c.receive_json_from(timeout=2)

            self.assertEqual(alice_event['type'], 'chat')
            self.assertEqual(alice_event['event'], 'message')
            self.assertEqual(alice_event['conversation_id'], self.conversation.pk)
            alice_message = alice_event['payload']['message']
            self.assertEqual(alice_message['text'], 'Hello via WS')
            self.assertEqual(alice_message['client_message_id'], 'abc123')
            self.assertEqual(alice_message['author_id'], self.alice.id)

            self.assertEqual(bob_event['event'], 'message')
            self.assertEqual(bob_event['payload']['message']['id'], alice_message['id'])
            await alice_c.disconnect()
            await bob_c.disconnect()

        _run_ws(scenario())
        self.assertEqual(Message.objects.filter(conversation=self.conversation).count(), 1)

    def test_duplicate_client_message_id_is_deduplicated(self):
        bob_c = self._communicator(self.bob)

        async def scenario():
            await self._connect(bob_c, self.bob)

            payload = {
                'type': 'send_message',
                'conversation_id': self.conversation.pk,
                'body': 'Dup',
                'client_message_id': 'dup-1',
            }
            await bob_c.send_json_to(payload)
            await bob_c.receive_json_from(timeout=2)
            await bob_c.send_json_to(payload)
            await asyncio.sleep(0.3)
            self.assertTrue(bob_c.output_queue.empty())
            await bob_c.disconnect()

        _run_ws(scenario())
        self.assertEqual(Message.objects.filter(conversation=self.conversation).count(), 1)

    def test_read_event_is_broadcast_and_persisted(self):
        alice_c = self._communicator(self.alice)
        bob_c = self._communicator(self.bob)
        Message.objects.create(conversation=self.conversation, author=self.bob, body='For alice')

        async def scenario():
            await self._connect(alice_c, self.alice)
            await self._connect(bob_c, self.bob)

            await alice_c.send_json_to({
                'type': 'read',
                'conversation_id': self.conversation.pk,
            })

            bob_event = await bob_c.receive_json_from(timeout=2)
            self.assertEqual(bob_event['event'], 'read')
            self.assertEqual(bob_event['payload']['user_id'], self.alice.id)
            await alice_c.disconnect()
            await bob_c.disconnect()

        _run_ws(scenario())
        self.assertEqual(MessageRead.objects.filter(user=self.alice, conversation=self.conversation).count(), 1)

    @override_settings(RATE_LIMIT_MESSAGES={'limit': 1, 'window': 300})
    def test_ws_send_message_is_rate_limited(self):
        cache.clear()
        alice_c = self._communicator(self.alice)

        async def scenario():
            await self._connect(alice_c, self.alice)

            await alice_c.send_json_to({
                'type': 'send_message',
                'conversation_id': self.conversation.pk,
                'body': 'First',
                'client_message_id': 'ws-rl-1',
            })
            first_event = await alice_c.receive_json_from(timeout=2)
            self.assertEqual(first_event['type'], 'chat')

            await alice_c.send_json_to({
                'type': 'send_message',
                'conversation_id': self.conversation.pk,
                'body': 'Second',
                'client_message_id': 'ws-rl-2',
            })
            error_event = await alice_c.receive_json_from(timeout=2)
            self.assertEqual(error_event['type'], 'error')
            self.assertIn('too quickly', error_event['error'])
            await alice_c.disconnect()

        _run_ws(scenario())
        self.assertEqual(Message.objects.filter(conversation=self.conversation).count(), 1)
