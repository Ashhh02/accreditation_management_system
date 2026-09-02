from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accreditation.models import (
    AccreditationArea,
    AccreditationCycle,
    AccreditationLevel,
    AccreditationSubArea,
    EvidenceRequirement,
)
from core.models import Department, Role, RoleAssignment, UserProfile


class DashboardDeadlinesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='PROGRAM_HEAD', name='Program Head')
        cls.department = Department.objects.create(code='TEST', name='Test Program', kind=Department.PROGRAM)
        cls.user = cls.make_user('dash-owner')

        cycle = AccreditationCycle.objects.create(
            name='Cycle', academic_year='2025-2026', status=AccreditationCycle.ACTIVE, is_active=True,
        )
        level = AccreditationLevel.objects.create(cycle=cycle, code='I', name='Level I')
        area = AccreditationArea.objects.create(level=level, code='Area I', name='Mission', slug='area-i')
        subarea = AccreditationSubArea.objects.create(area=area, code='1.1', title='Mission')
        cls.requirement = EvidenceRequirement.objects.create(
            area=area, subarea=subarea, code='1.1.1', title='Mission doc',
            required_description='Provide it.', deadline=timezone.localdate() + timedelta(days=10),
        )

    @classmethod
    def make_user(cls, username):
        user = get_user_model().objects.create_user(username=username, password='password')  # nosec B106 test fixture only
        profile = UserProfile.objects.create(user=user, department=cls.department, approval_status=UserProfile.APPROVED)
        assignment = RoleAssignment.objects.create(user=user, role=cls.role, department=cls.department, is_approved=True)
        profile.active_assignment = assignment
        profile.save(update_fields=['active_assignment'])
        return user

    def test_deadline_appears_in_dashboard_and_is_urgent(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        deadlines = response.context['upcoming_deadlines']
        self.assertTrue(deadlines)
        first = deadlines[0]
        self.assertIn(self.requirement.code, first['title'])
        self.assertTrue(first['urgent'])
