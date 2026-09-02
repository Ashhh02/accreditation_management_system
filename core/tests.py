from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Department, Notification, Role, RoleAssignment, UserProfile


class NotificationFeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        cls.department = Department.objects.create(code='TEST', name='Test Program', kind=Department.PROGRAM)
        cls.user = cls.make_user('core-owner')

    @classmethod
    def make_user(cls, username):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        profile = UserProfile.objects.create(user=user, department=cls.department, approval_status=UserProfile.APPROVED)
        assignment = RoleAssignment.objects.create(
            user=user, role=cls.role, department=cls.department, is_approved=True,
        )
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment'])
        return user

    def test_feed_returns_json_with_unread_count(self):
        Notification.objects.create(user=self.user, kind='workflow', title='First', message='Hi')
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:notification_feed'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        payload = response.json()
        self.assertEqual(payload['unread'], 1)
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(payload['items'][0]['title'], 'First')
        self.assertTrue(payload['items'][0]['unread'])

    def test_feed_requires_authentication(self):
        response = self.client.get(reverse('core:notification_feed'))
        self.assertEqual(response.status_code, 302)
