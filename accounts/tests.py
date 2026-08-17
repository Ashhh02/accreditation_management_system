from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Department, Role, RoleAssignment, UserProfile


class LoginPageTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        self.department = Department.objects.create(code='TEST', name='Test Program', kind=Department.PROGRAM)
        self.user = get_user_model().objects.create_user(
            username='qa-admin',
            email='qa-admin@jmcfi.edu.ph',
            password='safe-test-password',
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            department=self.department,
            approval_status=UserProfile.APPROVED,
        )
        self.assignment = RoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            department=self.department,
            is_approved=True,
        )
        self.profile.active_assignment = self.assignment
        self.profile.save(update_fields=['active_assignment'])

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_valid_credentials_redirect_to_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': self.user.username,
                'password': 'safe-test-password',
            },
        )

        self.assertRedirects(response, reverse('dashboard:index'))

    def test_email_credentials_redirect_to_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': self.user.email,
                'password': 'safe-test-password',
            },
        )

        self.assertRedirects(response, reverse('dashboard:index'))

    def test_registration_creates_pending_account_and_assignment(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-program-head',
            'email': 'new-program-head@jmcfi.edu.ph',
            'first_name': 'New',
            'last_name': 'Head',
            'role': self.role.id,
            'department': self.department.id,
            'password1': 'A-strong-registration-password-55!',
            'password2': 'A-strong-registration-password-55!',
        })
        self.assertEqual(response.status_code, 200)
        new_user = get_user_model().objects.get(username='new-program-head')
        self.assertFalse(new_user.is_active)
        self.assertEqual(new_user.profile.approval_status, UserProfile.PENDING)
        self.assertFalse(new_user.role_assignments.get().is_approved)

    def test_admin_can_approve_pending_account(self):
        admin_role = Role.objects.create(code='ADMIN', name='Admin')
        admin = get_user_model().objects.create_user(username='admin-user', password='admin-password')
        admin_profile = UserProfile.objects.create(
            user=admin,
            department=self.department,
            approval_status=UserProfile.APPROVED,
        )
        admin_assignment = RoleAssignment.objects.create(
            user=admin,
            role=admin_role,
            department=self.department,
            is_approved=True,
        )
        admin_profile.active_assignment = admin_assignment
        admin_profile.save(update_fields=['active_assignment'])
        pending = get_user_model().objects.create_user(username='pending-user', password='pending-password', is_active=False)
        pending_profile = UserProfile.objects.create(
            user=pending,
            department=self.department,
            approval_status=UserProfile.PENDING,
        )
        RoleAssignment.objects.create(user=pending, role=self.role, department=self.department, is_approved=False)

        self.client.force_login(admin)
        response = self.client.post(reverse('accounts:user_management'), {'action': 'approve', 'user_id': pending.id})
        self.assertRedirects(response, reverse('accounts:user_management'))
        pending.refresh_from_db()
        pending_profile.refresh_from_db()
        self.assertTrue(pending.is_active)
        self.assertEqual(pending_profile.approval_status, UserProfile.APPROVED)
        self.assertTrue(pending.role_assignments.get().is_approved)

    def test_profile_settings_are_saved_to_database(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:settings_profile'), {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@jmcfi.edu.ph',
        })
        self.assertRedirects(response, reverse('accounts:settings_profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), 'Updated User')
        self.assertEqual(self.user.email, 'updated@jmcfi.edu.ph')
