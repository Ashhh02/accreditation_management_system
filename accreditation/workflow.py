from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from core.access import assignment_for_reviewer, reviewer_assignments
from core.models import AuditLog, Role
from core.notifications import create_notification

from .models import EvidenceComment, EvidenceFile, EvidenceReview, EvidenceSubmission, EvidenceVersion


class WorkflowError(ValidationError):
    pass


def _role(code):
    return Role.objects.get(code=code)


def _audit(actor, submission, action, details=None):
    AuditLog.objects.create(
        actor=actor,
        submission=submission,
        action=action,
        object_type='EvidenceSubmission',
        object_id=str(submission.pk),
        details=details or {},
    )


def _evidence_url(submission):
    return reverse('accreditation:evidence_detail', args=[submission.pk])


def _notify(users, submission, title, message, kind='workflow'):
    target_url = _evidence_url(submission)
    seen = set()
    for user in users:
        if not user or not user.is_active or user.pk in seen:
            continue
        seen.add(user.pk)
        create_notification(
            user,
            kind=kind,
            title=title,
            message=message,
            submission=submission,
            entity_type='EvidenceSubmission',
            entity_id=str(submission.pk),
            target_url=target_url,
        )


def _next_version_number(submission):
    latest = submission.versions.order_by('-version_number').first()
    return (latest.version_number + 1) if latest else 1


def _save_version(submission, actor, self_evaluation, actual_situation, files=None, link_url='', change_remarks=''):
    submission.versions.filter(is_current=True).update(is_current=False, status=EvidenceVersion.SUPERSEDED)
    version = EvidenceVersion.objects.create(
        submission=submission,
        version_number=_next_version_number(submission),
        self_evaluation=self_evaluation,
        actual_situation=actual_situation,
        submitted_by=actor,
        status=EvidenceVersion.SUBMITTED,
        is_current=True,
        change_remarks=change_remarks,
    )
    for uploaded_file in files or []:
        EvidenceFile.objects.create(
            version=version,
            uploaded_by=actor,
            file=uploaded_file,
            original_name=uploaded_file.name,
            content_type=getattr(uploaded_file, 'content_type', ''),
            size=getattr(uploaded_file, 'size', None),
        )
    if link_url:
        EvidenceFile.objects.create(
            version=version,
            uploaded_by=actor,
            link_url=link_url,
            original_name=link_url,
        )
    return version


def _assign_next_reviewer(submission, role_code):
    candidates = reviewer_assignments(role_code, submission)
    reviewer = candidates.first()
    if not reviewer:
        raise WorkflowError(f'No approved {role_code.replace("_", " ").title()} is assigned to this submission.')
    submission.current_reviewer = reviewer.user
    submission.current_review_role = reviewer.role
    return reviewer.user


@transaction.atomic
def save_draft(submission, actor, self_evaluation, actual_situation):
    if submission.program_head_id != actor.id:
        raise PermissionDenied('You can only manage evidence assigned to your program.')
    if submission.status not in {EvidenceSubmission.DRAFT, EvidenceSubmission.NEEDS_REVISION}:
        raise WorkflowError('Only draft or revision-requested evidence can be edited.')
    submission.self_evaluation = self_evaluation
    submission.actual_situation = actual_situation
    submission.last_updated_by = actor
    submission.save()
    _audit(actor, submission, 'DRAFT_SAVED', {'status': submission.status})
    return submission


@transaction.atomic
def submit_submission(submission, actor, self_evaluation, actual_situation, files=None, link_url='', change_remarks=''):
    if submission.program_head_id != actor.id:
        raise PermissionDenied('You can only manage evidence assigned to your program.')
    if submission.status not in {EvidenceSubmission.DRAFT, EvidenceSubmission.NEEDS_REVISION}:
        raise WorkflowError('Only draft or revision-requested evidence can be submitted.')
    if not (self_evaluation or '').strip() or not (actual_situation or '').strip():
        raise WorkflowError('Self-evaluation and actual situation are required before submission.')
    if not files and not link_url and not EvidenceFile.objects.filter(version__submission=submission).exists():
        raise WorkflowError('Add at least one supporting document or link before submission.')

    previous_status = submission.status
    version = _save_version(
        submission,
        actor,
        self_evaluation,
        actual_situation,
        files=files,
        link_url=link_url,
        change_remarks=change_remarks,
    )
    submission.self_evaluation = self_evaluation
    submission.actual_situation = actual_situation
    submission.last_updated_by = actor
    submission.submitted_at = submission.submitted_at or timezone.now()

    if previous_status == EvidenceSubmission.NEEDS_REVISION:
        if not submission.revision_return_reviewer_id or not submission.revision_return_role_id:
            raise WorkflowError('This revision request has no assigned return reviewer.')
        target_status = submission.revision_return_status
        submission.status = target_status
        submission.current_reviewer = submission.revision_return_reviewer
        submission.current_review_role = submission.revision_return_role
        submission.revision_return_status = ''
        submission.revision_return_reviewer = None
        submission.revision_return_role = None
        reviewer = submission.current_reviewer
    else:
        submission.status = EvidenceSubmission.UNDER_DEAN_REVIEW
        reviewer = _assign_next_reviewer(submission, 'DEAN')

    submission.save()
    _audit(actor, submission, 'SUBMITTED', {
        'version': version.version_number,
        'from_status': previous_status,
        'to_status': submission.status,
    })
    _notify(
        [reviewer],
        submission,
        'Evidence submitted for review',
        f'{submission.requirement.code} is ready for your review.',
        kind='submission',
    )
    return submission


def _assert_current_reviewer(submission, actor):
    if submission.current_reviewer_id != actor.id:
        raise PermissionDenied('You are not the reviewer currently assigned to this submission.')
    if not submission.current_review_role_id or not assignment_for_reviewer(actor, submission):
        raise PermissionDenied('Your role or department is not authorized for this review.')


@transaction.atomic
def approve_submission(submission, actor, remarks=''):
    _assert_current_reviewer(submission, actor)
    old_status = submission.status
    current_role = submission.current_review_role

    auto_close = False
    if old_status == EvidenceSubmission.UNDER_DEAN_REVIEW:
        next_status, next_role = EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW, 'AREA_CHAIR'
        decision = EvidenceReview.APPROVED
        next_reviewer = _assign_next_reviewer(submission, next_role)
    elif old_status == EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW:
        next_status, next_role = EvidenceSubmission.UNDER_QA_REVIEW, 'QA'
        decision = EvidenceReview.APPROVED
        try:
            next_reviewer = _assign_next_reviewer(submission, next_role)
        except WorkflowError:
            next_status, next_role = EvidenceSubmission.UNDER_QA_REVIEW, 'ACCREDITATION_HEAD'
            next_reviewer = _assign_next_reviewer(submission, next_role)
    elif old_status == EvidenceSubmission.UNDER_QA_REVIEW:
        next_status, next_role = EvidenceSubmission.COMPLIED, None
        decision = EvidenceReview.COMPLIED_DECISION
        next_reviewer = None
        submission.closed_at = timezone.now()
        auto_close = True
    else:
        raise WorkflowError('This submission is not awaiting an approval decision.')

    EvidenceReview.objects.create(
        submission=submission,
        version=submission.latest_version,
        reviewer=actor,
        reviewer_role=current_role,
        from_status=old_status,
        to_status=next_status,
        decision=decision,
        remarks=remarks,
    )
    submission.status = next_status
    submission.current_reviewer = next_reviewer
    submission.current_review_role = _role(next_role) if next_role else None
    submission.last_updated_by = actor
    submission.save()
    _audit(actor, submission, decision, {'from_status': old_status, 'to_status': next_status})

    if auto_close:
        EvidenceReview.objects.create(
            submission=submission,
            version=submission.latest_version,
            reviewer=actor,
            reviewer_role=current_role,
            from_status=EvidenceSubmission.COMPLIED,
            to_status=EvidenceSubmission.CLOSED,
            decision=EvidenceReview.CLOSED_DECISION,
            remarks='Automatically closed after final internal compliance approval.',
        )
        submission.status = EvidenceSubmission.CLOSED
        submission.current_reviewer = None
        submission.current_review_role = None
        submission.save(update_fields=['status', 'current_reviewer', 'current_review_role', 'last_updated', 'closed_at'])
        submission.versions.filter(is_current=True).update(status=EvidenceVersion.APPROVED)
        _audit(actor, submission, 'CLOSED', {'from_status': EvidenceSubmission.COMPLIED, 'to_status': EvidenceSubmission.CLOSED})

    if next_reviewer:
        _notify(
            [next_reviewer],
            submission,
            'New review task assigned',
            f'{submission.requirement.code} passed {current_role.name} review and is now assigned to you.',
            kind='task',
        )
    else:
        _notify(
            [submission.program_head],
            submission,
            'Evidence complied and closed',
            f'{submission.requirement.code} completed the internal review workflow.',
            kind='review',
        )
    return submission


@transaction.atomic
def request_revision(submission, actor, remarks):
    _assert_current_reviewer(submission, actor)
    if not remarks or not remarks.strip():
        raise WorkflowError('Remarks are required when requesting a revision.')
    if submission.status not in {
        EvidenceSubmission.UNDER_DEAN_REVIEW,
        EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW,
        EvidenceSubmission.UNDER_QA_REVIEW,
    }:
        raise WorkflowError('This submission is not awaiting a review decision.')

    old_status = submission.status
    current_role = submission.current_review_role
    EvidenceReview.objects.create(
        submission=submission,
        version=submission.latest_version,
        reviewer=actor,
        reviewer_role=current_role,
        from_status=old_status,
        to_status=EvidenceSubmission.NEEDS_REVISION,
        decision=EvidenceReview.REQUEST_REVISION,
        remarks=remarks.strip(),
    )
    submission.revision_return_status = old_status
    submission.revision_return_reviewer = actor
    submission.revision_return_role = current_role
    submission.status = EvidenceSubmission.NEEDS_REVISION
    submission.current_reviewer = submission.program_head
    submission.current_review_role = _role('PROGRAM_HEAD')
    submission.last_updated_by = actor
    submission.save()
    submission.versions.filter(is_current=True).update(status=EvidenceVersion.NOT_APPROVED)
    EvidenceComment.objects.create(
        submission=submission,
        version=submission.latest_version,
        author=actor,
        body=remarks.strip(),
    )
    _audit(actor, submission, 'REQUEST_REVISION', {'from_status': old_status, 'remarks': remarks.strip()})
    _notify(
        [submission.program_head],
        submission,
        'Revision requested',
        f'{submission.requirement.code} needs revision before it can continue.',
        kind='revision',
    )
    return submission


@transaction.atomic
def mark_non_complied(submission, actor, remarks):
    _assert_current_reviewer(submission, actor)
    if not remarks or not remarks.strip():
        raise WorkflowError('Remarks are required when marking evidence non-complied.')
    if submission.status != EvidenceSubmission.UNDER_QA_REVIEW or submission.current_review_role.code not in {'QA', 'ACCREDITATION_HEAD'}:
        raise WorkflowError('Only QA or the Accreditation Head can mark evidence non-complied.')
    old_status = submission.status
    current_role = submission.current_review_role
    EvidenceReview.objects.create(
        submission=submission,
        version=submission.latest_version,
        reviewer=actor,
        reviewer_role=current_role,
        from_status=old_status,
        to_status=EvidenceSubmission.NON_COMPLIED,
        decision=EvidenceReview.NON_COMPLIED_DECISION,
        remarks=remarks.strip(),
    )
    submission.status = EvidenceSubmission.NON_COMPLIED
    submission.current_reviewer = None
    submission.current_review_role = None
    submission.last_updated_by = actor
    submission.save()
    submission.versions.filter(is_current=True).update(status=EvidenceVersion.NOT_APPROVED)
    EvidenceComment.objects.create(
        submission=submission,
        version=submission.latest_version,
        author=actor,
        body=remarks.strip(),
    )
    _audit(actor, submission, 'NON_COMPLIED', {'from_status': old_status, 'remarks': remarks.strip()})
    _notify(
        [submission.program_head],
        submission,
        'Evidence marked non-complied',
        f'{submission.requirement.code} was marked non-complied after internal review.',
        kind='review',
    )
    return submission
