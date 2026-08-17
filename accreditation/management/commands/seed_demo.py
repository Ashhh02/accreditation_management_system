from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accreditation.evidence_data import EVIDENCE_ITEMS
from accreditation.models import (
    AccreditationArea,
    AccreditationCycle,
    AccreditationLevel,
    AccreditationSubArea,
    EvidenceRequirement,
)
from accreditation.views import AREA_SUBAREAS
from core.models import Department, Role, RoleAssignment, UserProfile


ROLE_DEFINITIONS = [
    ('SUPERADMIN', 'Superadmin'),
    ('ADMIN', 'Admin'),
    ('QA', 'QA'),
    ('ACCREDITATION_HEAD', 'Accreditation Head'),
    ('PROGRAM_HEAD', 'Program Head'),
    ('DEAN', 'Dean'),
    ('AREA_CHAIR', 'Area Chair'),
    ('STUDENT', 'Student'),
]


DEPARTMENT_DEFINITIONS = [
    ('QA', 'QA Office', Department.OFFICE, None),
    ('ENG', 'College of Engineering', Department.DEPARTMENT, None),
    ('ENG-BSCIV', 'Bachelor of Science in Civil Engineering', Department.PROGRAM, 'ENG'),
    ('BUS', 'College of Business', Department.DEPARTMENT, None),
    ('EDU', 'College of Education', Department.DEPARTMENT, None),
    ('NURS', 'College of Nursing', Department.DEPARTMENT, None),
]


DEMO_USERS = [
    ('demo-superadmin', 'superadmin@jmcfi.edu.ph', 'Demo', 'Superadmin', 'SUPERADMIN', 'QA'),
    ('demo-admin', 'admin@jmcfi.edu.ph', 'Demo', 'Admin', 'ADMIN', 'QA'),
    ('demo-qa', 'qa@jmcfi.edu.ph', 'Demo', 'QA', 'QA', 'QA'),
    ('demo-accreditation-head', 'accreditation.head@jmcfi.edu.ph', 'Demo', 'Accreditation Head', 'ACCREDITATION_HEAD', 'QA'),
    ('demo-program-head', 'program.head@jmcfi.edu.ph', 'Demo', 'Program Head', 'PROGRAM_HEAD', 'ENG-BSCIV'),
    ('demo-dean', 'dean@jmcfi.edu.ph', 'Demo', 'Dean', 'DEAN', 'ENG'),
    ('demo-area-chair', 'area.chair@jmcfi.edu.ph', 'Demo', 'Area Chair', 'AREA_CHAIR', 'ENG'),
]


class Command(BaseCommand):
    help = 'Seed the internal accreditation structure and development demo accounts.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError('Demo seeding is disabled when DEMO_MODE is false.')

        roles = {}
        for sort_order, (code, name) in enumerate(ROLE_DEFINITIONS):
            role, _ = Role.objects.update_or_create(
                code=code,
                defaults={'name': name, 'is_internal': True, 'is_active': True, 'sort_order': sort_order},
            )
            roles[code] = role

        departments = {}
        for code, name, kind, parent_code in DEPARTMENT_DEFINITIONS:
            parent = departments.get(parent_code)
            department, _ = Department.objects.update_or_create(
                code=code,
                defaults={'name': name, 'kind': kind, 'parent': parent, 'is_active': True},
            )
            departments[code] = department

        cycle, _ = AccreditationCycle.objects.update_or_create(
            academic_year='2025-2026',
            defaults={
                'name': 'PACUCOA Accreditation Cycle',
                'status': AccreditationCycle.ACTIVE,
                'is_active': True,
            },
        )
        level_names = [
            ('I', 'Level I', 'Candidate Status'),
            ('II', 'Level II', 'Accredited Status'),
            ('III', 'Level III', 'Accredited Status II'),
            ('IV', 'Level IV', 'Accredited Status III'),
        ]
        levels = {}
        for order, (code, name, status_label) in enumerate(level_names):
            level, _ = AccreditationLevel.objects.update_or_create(
                cycle=cycle,
                code=code,
                defaults={'name': name, 'status_label': status_label, 'sort_order': order},
            )
            levels[code] = level

        areas = []
        for order, (area_key, area_data) in enumerate(AREA_SUBAREAS.items()):
            area_number = area_data['code'].split()[-1]
            area, _ = AccreditationArea.objects.update_or_create(
                level=levels['I'],
                code=area_data['code'],
                defaults={
                    'name': area_data['name'],
                    'slug': area_key,
                    'sort_order': order,
                },
            )
            areas.append(area)
            subareas_by_code = {}
            for sub_order, subarea in enumerate(area_data['subareas']):
                subarea_obj, _ = AccreditationSubArea.objects.update_or_create(
                    area=area,
                    code=subarea['code'],
                    defaults={'title': subarea['title'], 'sort_order': sub_order},
                )
                subareas_by_code[subarea['code']] = subarea_obj
                for evidence_order, (evidence_code, evidence_title) in enumerate(EVIDENCE_ITEMS.get(subarea['code'], ())):
                    EvidenceRequirement.objects.update_or_create(
                        area=area,
                        code=evidence_code,
                        defaults={
                            'subarea': subarea_obj,
                            'title': evidence_title,
                            'required_description': f'Supporting evidence for {evidence_title}.',
                            'sort_order': evidence_order,
                            'is_required': True,
                        },
                    )

        User = get_user_model()
        demo_assignments = {}
        for username, email, first_name, last_name, role_code, department_code in DEMO_USERS:
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.is_staff = role_code in {'SUPERADMIN', 'ADMIN'}
            user.is_superuser = role_code == 'SUPERADMIN'
            user.set_password('123')
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.department = departments[department_code]
            profile.approval_status = UserProfile.APPROVED
            profile.is_demo_account = True
            profile.must_change_password = True
            profile.save()

            assignment, _ = RoleAssignment.objects.update_or_create(
                user=user,
                role=roles[role_code],
                department=departments[department_code],
                defaults={
                    'is_approved': True,
                    'approved_by': None,
                },
            )
            assignment.assigned_areas.set(areas if role_code == 'AREA_CHAIR' else [])
            demo_assignments[username] = assignment
            profile.active_assignment = assignment
            profile.save(update_fields=['active_assignment', 'updated_at'])

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(roles)} internal roles, {len(departments)} departments/programs, '
            f'{len(areas)} areas, and {len(DEMO_USERS)} demo accounts.'
        ))
        self.stdout.write('Demo accounts are marked for password change and use the development-only password 123.')
