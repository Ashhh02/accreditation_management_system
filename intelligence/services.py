"""Real AI / decision-support engine.

Everything here reads the live accreditation database from the caller's access
scope. When AI_BASE_URL + AI_API_KEY are configured, answers are composed by an
OpenAI-compatible chat-completions provider on top of the retrieved facts
(grounded RAG). Without a provider the engine answers deterministically from
the same facts, so the feature never depends on an external service.
"""

import json
import logging
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from accreditation.models import AccreditationCycle, AccreditationLevel, EvidenceRequirement, EvidenceSubmission, EvidenceVersion
from core.access import accessible_submissions, department_scope_ids
from core.models import Department

logger = logging.getLogger(__name__)

COMPLETED_STATUSES = {EvidenceSubmission.COMPLIED, EvidenceSubmission.CLOSED}
ACTIVE_REVIEW_STATUSES = {
    EvidenceSubmission.UNDER_DEAN_REVIEW,
    EvidenceSubmission.UNDER_AREA_CHAIR_REVIEW,
    EvidenceSubmission.UNDER_QA_REVIEW,
}
REVISION_STATUS = EvidenceSubmission.NEEDS_REVISION

AVA_PERSONA = (
    'You are AVA, the JMCFI Quality Assurance Accreditation Virtual Assistant. '
    'You give advisory guidance on internal accreditation preparation for Philippine higher '
    'education, aligned with the CHED FAQs, PACUCOA, PAASCU, and AACCUP accreditation '
    'frameworks. Answer ONLY from the supplied Facts; never invent numbers, item codes, or '
    'dates. Where the facts are insufficient, say so and suggest a follow-up question. Be '
    'concise, professional, and supportive. Use short bullets when listing items and mark '
    'all suggestions as advisory — formal decisions rest with the accrediting body.'
)


def summary(user):
    """Headline metrics for the active user's access scope."""
    submissions = accessible_submissions(user)
    total = submissions.count()
    completed = submissions.filter(status__in=COMPLETED_STATUSES).count()
    pending = submissions.filter(status__in=ACTIVE_REVIEW_STATUSES).count()
    revisions = submissions.filter(status=REVISION_STATUS).count()
    drafts = submissions.filter(status=EvidenceSubmission.DRAFT).count()
    submitted = submissions.exclude(status=EvidenceSubmission.DRAFT).count()
    readiness = round(completed * 100 / total, 1) if total else 0.0
    compliance = round(completed * 100 / submitted, 1) if submitted else 0.0
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'revisions': revisions,
        'drafts': drafts,
        'submitted': submitted,
        'readiness': readiness,
        'compliance': compliance,
    }


def departments(user):
    """Per-department compliance rows for the access scope."""
    submissions = accessible_submissions(user)
    rows = []
    for department in Department.objects.filter(is_active=True, kind=Department.DEPARTMENT).order_by('name'):
        scoped = submissions.filter(department_id__in=department_scope_ids(department))
        submitted = scoped.exclude(status=EvidenceSubmission.DRAFT).count()
        compiled = scoped.filter(status__in=COMPLETED_STATUSES).count()
        if not submitted and not scoped.exists():
            continue
        rate = round(compiled * 100 / submitted) if submitted else 0
        rows.append({
            'name': department.name,
            'submitted': submitted,
            'compiled': compiled,
            'compliance': rate,
            'status': 'On Track' if rate >= 80 else 'At Risk' if rate >= 50 else 'Critical',
            'tone': 'green' if rate >= 80 else 'gold' if rate >= 50 else 'rose',
        })
    return rows


def risk_recommendations(user):
    """Risk matrix: weighted gaps across departments with an explicit recommendation."""
    rows = []
    for department in departments(user):
        if department['submitted'] == 0:
            continue
        gap = 100 - department['compliance']
        overdue = _overdue_counts(user).get(department['name'], 0)
        revisions = _revision_counts(user).get(department['name'], 0)
        score = gap + min(overdue, 100) * 0.5 + min(revisions, 100) * 0.3
        if score >= 120:
            severity, tone, label = 'High', 'rose', 'Critical'
        elif score >= 60:
            severity, tone, label = 'Medium', 'gold', 'At Risk'
        else:
            severity, tone, label = 'Low', 'green', 'On Track'
        rows.append({
            'department': department['name'],
            'compliance': department['compliance'],
            'overdue': overdue,
            'revisions': revisions,
            'severity': severity,
            'tone': tone,
            'label': label,
            'recommendation': _recommendation_for(severity, department['name'], overdue, revisions, gap),
        })
    return sorted(rows, key=lambda item: {'High': 0, 'Medium': 1, 'Low': 2}[item['severity']])


def ai_insights(user):
    """Curated advisory insights for the AI Insights page (AVA assessment)."""
    data = summary(user)
    submissions = accessible_submissions(user)
    insights = [
        {
            'title': 'Overall Readiness',
            'description': f"{data['readiness']}% of visible evidence is complied or closed ({data['completed']} of {data['total']}).",
            'tone': 'green' if data['readiness'] >= 80 else 'gold',
            'icon': 'trend-up',
        },
        {
            'title': 'Pending Internal Review',
            'description': f"{data['pending']} item(s) are waiting on an assigned reviewer across the workflow stages.",
            'tone': 'gold',
            'icon': 'clock',
        },
        {
            'title': 'Revision Queue',
            'description': (
                f"{data['revisions']} item(s) were returned to Program Heads for correction."
                if data['revisions'] else 'Nothing is currently sitting in the revision queue.'
            ),
            'tone': 'rose' if data['revisions'] else 'green',
            'icon': 'alert' if data['revisions'] else 'check',
        },
    ]

    area_coverage = _area_coverage(user, submissions)
    weak_area = min(area_coverage, key=lambda item: item['rate']) if area_coverage else None
    if weak_area:
        insights.append({
            'title': 'Lowest Readiness Area',
            'description': f"{weak_area['code']} ({weak_area['name']}) is at {weak_area['rate']}% — prioritize these requirements first.",
            'tone': weak_area['tone'],
            'icon': 'shield',
        })

    risks = risk_recommendations(user)
    top_risk = next((row for row in risks if row['severity'] == 'High'), None) or (risks[0] if risks else None)
    if top_risk:
        insights.append({
            'title': f'Top Department Risk: {top_risk["department"]}',
            'description': top_risk['recommendation'],
            'tone': top_risk['tone'],
            'icon': 'alert',
        })

    today = timezone.localdate()
    in_scope = submissions.exclude(status__in=COMPLETED_STATUSES)
    overdue = in_scope.filter(requirement__deadline__lt=today).count()
    due_soon = in_scope.filter(requirement__deadline__gte=today, requirement__deadline__lte=today + timedelta(days=60)).count()
    if overdue or due_soon:
        insights.append({
            'title': 'Deadline Pressure',
            'description': (
                f'{overdue} overdue item(s) and {due_soon} due within 60 days. '
                + ('Clear the overdue queue first to avoid compounding gaps.' if overdue else 'Keep the submission calendar on track.')
            ),
            'tone': 'rose' if overdue else 'gold',
            'icon': 'clock',
        })

    version_activity = submissions.filter(versions__isnull=False).annotate(version_count=Count('versions')).filter(version_count__gt=1).count()
    superseded = EvidenceVersion.objects.filter(submission__in=submissions, status=EvidenceVersion.SUPERSEDED).count()
    insights.append({
        'title': 'Document Versioning',
        'description': (
            f'{version_activity} submission(s) have multiple versions on record; {superseded} older version(s) were superseded. '
            'Version history preserves every revision for audit and review.'
        ),
        'tone': 'green' if version_activity else 'slate',
        'icon': 'layers',
    })

    assessment = (
        f'AVA assessment: readiness stands at {data["readiness"]}% across your scope with '
        f'{data["pending"]} item(s) in review and {data["revisions"]} needing revision.'
    )
    if weak_area:
        assessment += f' The biggest gap is {weak_area["code"]} ({weak_area["name"]}) at {weak_area["rate"]}% coverage.'
    if top_risk:
        assessment += f' Highest exposure is {top_risk["department"]}.'
    if overdue:
        assessment += f' {overdue} item(s) are already past deadline.'
    assessment += ' Prepared in the spirit of CHED-aligned internal readiness review; treat this as advisory, not an accreditor decision.'

    return {
        'insights': insights,
        'assessment': assessment,
        'areas': area_coverage,
        'top_risk': top_risk,
        'risks': risks[:6],
        'summary': data,
    }


def _area_coverage(user, submissions):
    """Coverage ratio per area of the active cycle's level I, for the AI Insights page."""
    cycle = AccreditationCycle.objects.filter(is_active=True).first()
    level = AccreditationLevel.objects.filter(cycle=cycle).filter(code='I').first() if cycle else None
    rows = []
    if level:
        for area in level.areas.all():
            required = EvidenceRequirement.objects.filter(area=area).count()
            done = submissions.filter(requirement__area=area, status__in=COMPLETED_STATUSES).count()
            rate = round(done * 100 / required) if required else 0
            rows.append({
                'code': area.code,
                'name': area.name,
                'rate': rate,
                'tone': 'green' if rate >= 80 else 'gold' if rate >= 50 else 'rose',
            })
    return rows


def _overdue_counts(user):
    counts = {
        d['name']: 0
        for d in departments(user)
    }
    today = timezone.localdate()
    for submission in accessible_submissions(user).exclude(status__in=COMPLETED_STATUSES).select_related('requirement', 'department'):
        deadline = submission.requirement.deadline
        if deadline and deadline < today:
            counts[submission.department.name] = counts.get(submission.department.name, 0) + 1
    return counts


def _revision_counts(user):
    counts = {
        d['name']: 0
        for d in departments(user)
    }
    for submission in accessible_submissions(user).filter(status=REVISION_STATUS).select_related('department'):
        counts[submission.department.name] = counts.get(submission.department.name, 0) + 1
    return counts


def _recommendation_for(severity, name, overdue, revisions, gap):
    if severity == 'High':
        return f'Prioritize {name}: {overdue} overdue item(s) and {revisions} open revision(s), {gap}% gap from full compliance.'
    if severity == 'Medium':
        return f'Follow up with {name}: close {revisions} revision(s) and confirm {overdue} soon-due item(s).'
    return f'Maintain current pace; {name} is on track with {100 - gap}% compliance.'


def retrieve(user, question):
    """Route the question to a retrieval intent and return grounded facts."""
    text = (question or '').lower()

    if any(word in text for word in ('revision', 'revise', 'returned', 'fix', 'correct', 'redo', 'resubmit', 'correction')):
        return _revision_facts(user)
    if any(word in text for word in ('missing', 'not yet', 'draft', 'upload', 'incomplete', 'no evidence', 'document')):
        return _missing_facts(user)
    if any(word in text for word in ('deadline', 'due', 'overdue', 'on time', 'schedule')):
        return _deadline_facts(user)
    if any(word in text for word in ('pending', 'review', 'approve', 'queued', 'waiting', 'dean', 'area chair', 'qa')):
        return _pending_facts(user)
    if any(word in text for word in ('risk', 'critical', 'gap', 'warning', 'weak', 'threat', 'danger')):
        return _risk_facts(user)
    if any(word in text for word in ('department', 'program', 'office', 'college')):
        return _department_facts(user)
    if any(word in text for word in ('area', 'readiness', 'complied', 'compliance', 'summary', 'status', 'all')):
        return _area_facts(user)
    return _summary_facts(user)


def _revision_facts(user):
    items = list(accessible_submissions(user).filter(status=REVISION_STATUS).select_related(
        'requirement', 'requirement__area', 'department',
    ).order_by('-last_updated', '-id')[:6])
    summary_text = f'{len(items)} visible evidence item(s) currently need revision.'
    facts = []
    for item in items:
        latest = item.reviews.filter(decision='REQUEST_REVISION').order_by('-created_at').first()
        facts.append({
            'code': item.requirement.code,
            'title': item.requirement.title,
            'department': item.department.name,
            'status': 'Needs Revision',
            'notes': (latest.remarks if latest else '')[:180],
        })
    return {'intent': 'revision', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _missing_facts(user):
    submissions = accessible_submissions(user)
    total = submissions.count()
    missing = submissions.filter(status=EvidenceSubmission.DRAFT).count()
    not_started = submissions.exclude(status__in=COMPLETED_STATUSES).count()
    summary_text = f'{missing} of {total} visible item(s) are still drafts; {not_started} are not yet complied or closed.'
    items = list(submissions.filter(status=EvidenceSubmission.DRAFT).select_related(
        'requirement', 'requirement__area', 'department',
    ).order_by('requirement__deadline', 'requirement__code')[:6])
    facts = [{
        'code': item.requirement.code,
        'title': item.requirement.title,
        'department': item.department.name,
        'status': 'Draft / Not Yet Submitted',
    } for item in items]
    return {'intent': 'missing', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _deadline_facts(user):
    submissions = accessible_submissions(user).select_related('requirement', 'department')
    today = timezone.localdate()
    rows = []
    for submission in submissions:
        deadline = submission.requirement.deadline
        if not deadline:
            continue
        if submission.status in COMPLETED_STATUSES:
            continue
        state = 'OVERDUE' if deadline < today else 'DUE SOON'
        rows.append({
            'code': submission.requirement.code,
            'title': submission.requirement.title,
            'department': submission.department.name,
            'state': state,
            'deadline': deadline.isoformat(),
            'days': (deadline - today).days if deadline >= today else None,
        })
    rows.sort(key=lambda row: (0 if row['state'] == 'OVERDUE' else 1, row['deadline']))
    overdue = sum(1 for row in rows if row['state'] == 'OVERDUE')
    summary_text = f'{overdue} item(s) are past their deadline and {len(rows) - overdue} are due within 60 days.'
    return {
        'intent': 'deadlines',
        'headline': summary_text,
        'facts': rows[:8],
        'sources': [{'title': f"{row['code']} · {row['department']} · {row['state']}", 'url': ''} for row in rows[:5]],
    }


def _pending_facts(user):
    items = list(accessible_submissions(user).filter(status__in=ACTIVE_REVIEW_STATUSES).select_related(
        'requirement', 'department', 'current_reviewer', 'current_review_role',
    ).order_by('last_updated')[:6])
    summary_text = f'{len(items)} item(s) are waiting on an assigned internal reviewer.'
    facts = [{
        'code': item.requirement.code,
        'title': item.requirement.title,
        'department': item.department.name,
        'status': item.get_status_display(),
        'reviewer': f"{item.current_reviewer.get_full_name() or item.current_reviewer.username} ({item.current_review_role.name if item.current_review_role else 'unassigned'})",
    } for item in items]
    return {'intent': 'pending', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _risk_facts(user):
    recommendations = risk_recommendations(user)[:6]
    top = next((item for item in recommendations if item['severity'] == 'High'), recommendations[0] if recommendations else None)
    headline = (
        f"Top risk: {top['department']} ({top['label']})."
        if top else
        'No high-risk gaps detected in your access scope.'
    )
    facts = [{
        'department': row['department'],
        'severity': row['severity'],
        'compliance': f"{row['compliance']}%",
        'recommendation': row['recommendation'],
    } for row in recommendations]
    return {'intent': 'risks', 'headline': headline, 'facts': facts, 'sources': []}


def _department_facts(user):
    rows = departments(user)
    headline = f'{len(rows)} department(s) in scope; the lowest is {min(rows, key=lambda row: row["compliance"])["name"]} at {min(rows, key=lambda row: row["compliance"])["compliance"]}% compliance.' if rows else 'No department data in scope.'
    facts = [{
        'department': row['name'],
        'compliance': f"{row['compliance']}%",
        'status': row['status'],
    } for row in rows]
    return {'intent': 'departments', 'headline': headline, 'facts': facts, 'sources': []}


def _area_facts(user):
    data = summary(user)
    level = AccreditationLevel.objects.filter(cycle=AccreditationCycle.objects.filter(is_active=True).first()).filter(code='I').first()
    headlines = [
        f"Overall readiness is {data['readiness']}% ({data['completed']} of {data['total']} visible item(s) complied or closed).",
        f"{data['pending']} item(s) are in review and {data['revisions']} need revision.",
    ]
    facts = []
    if level:
        submissions = accessible_submissions(user)
        for area in level.areas.all():
            required = EvidenceRequirement.objects.filter(area=area).count()
            done = submissions.filter(requirement__area=area, status__in=COMPLETED_STATUSES).count()
            rate = round(done * 100 / required) if required else 0
            facts.append({'area': area.name, 'coverage': f'{rate}%', 'done': done, 'required': required})
    return {'intent': 'readiness', 'headline': ' '.join(headlines), 'facts': facts, 'sources': []}


def _summary_facts(user):
    data = summary(user)
    headline = (
        f"Across your scope: {data['readiness']}% readiness, {data['total']} visible submission(s), "
        f"{data['pending']} in review, {data['revisions']} needing revision, {data['drafts']} still drafts."
    )
    facts = [{'area': 'Readiness', 'value': f"{data['readiness']}%"}, {'area': 'In Review', 'value': data['pending']},
             {'area': 'Needs Revision', 'value': data['revisions']}, {'area': 'Drafts', 'value': data['drafts']}]
    return {'intent': 'summary', 'headline': headline, 'facts': facts, 'sources': []}


def _sources(submissions):
    sources = []
    for submission in submissions[:5]:
        sources.append({
            'title': f'{submission.requirement.code} · {submission.requirement.title[:60]} · {submission.department.name}',
            'url': reverse('accreditation:evidence_detail', args=[submission.pk]),
        })
    return sources


def _intent_revisions(user, question):
    items = list(accessible_submissions(user).filter(status=REVISION_STATUS).select_related(
        'requirement', 'requirement__area', 'department',
    ).order_by('-last_updated', '-id')[:6])
    summary_text = f'{len(items)} visible evidence item(s) currently need revision.'
    facts = []
    for item in items:
        latest = item.reviews.filter(decision='REQUEST_REVISION').order_by('-created_at').first()
        facts.append({
            'code': item.requirement.code,
            'title': item.requirement.title,
            'department': item.department.name,
            'status': 'Needs Revision',
            'notes': (latest.remarks if latest else '')[:180],
        })
    return {'intent': 'revision', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _intent_missing(user, question):
    submissions = accessible_submissions(user)
    total = submissions.count()
    missing = submissions.filter(status=EvidenceSubmission.DRAFT).count()
    not_started = submissions.exclude(status__in=COMPLETED_STATUSES).count()
    summary_text = f'{missing} of {total} visible item(s) are still drafts; {not_started} are not yet complied or closed.'
    items = list(submissions.filter(status=EvidenceSubmission.DRAFT).select_related(
        'requirement', 'requirement__area', 'department',
    ).order_by('requirement__deadline', 'requirement__code')[:6])
    facts = [{
        'code': item.requirement.code,
        'title': item.requirement.title,
        'department': item.department.name,
        'status': 'Draft / Not Yet Submitted',
    } for item in items]
    return {'intent': 'missing', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _intent_deadlines(user, question):
    submissions = accessible_submissions(user).select_related('requirement', 'department')
    today = timezone.localdate()
    rows = []
    for submission in submissions:
        deadline = submission.requirement.deadline
        if not deadline:
            continue
        if submission.status in COMPLETED_STATUSES:
            continue
        state = 'OVERDUE' if deadline < today else 'DUE SOON'
        rows.append({
            'code': submission.requirement.code,
            'title': submission.requirement.title,
            'department': submission.department.name,
            'state': state,
            'deadline': deadline.isoformat(),
            'days': (deadline - today).days if deadline >= today else None,
        })
    rows.sort(key=lambda row: (0 if row['state'] == 'OVERDUE' else 1, row['deadline']))
    overdue = sum(1 for row in rows if row['state'] == 'OVERDUE')
    summary_text = f'{overdue} item(s) are past their deadline and {len(rows) - overdue} are due within 60 days.'
    return {
        'intent': 'deadlines',
        'headline': summary_text,
        'facts': rows[:8],
        'sources': [{'title': f"{row['code']} · {row['department']} · {row['state']}", 'url': ''} for row in rows[:5]],
    }


def _intent_pending(user, question):
    items = list(accessible_submissions(user).filter(status__in=ACTIVE_REVIEW_STATUSES).select_related(
        'requirement', 'department', 'current_reviewer', 'current_review_role',
    ).order_by('last_updated')[:6])
    summary_text = f'{len(items)} item(s) are waiting on an assigned internal reviewer.'
    facts = [{
        'code': item.requirement.code,
        'title': item.requirement.title,
        'department': item.department.name,
        'status': item.get_status_display(),
        'reviewer': f"{item.current_reviewer.get_full_name() or item.current_reviewer.username} ({item.current_review_role.name if item.current_review_role else 'unassigned'})",
    } for item in items]
    return {'intent': 'pending', 'headline': summary_text, 'facts': facts, 'sources': _sources(items)}


def _intent_risks(user, question):
    recommendations = risk_recommendations(user)[:6]
    top = next((item for item in recommendations if item['severity'] == 'High'), recommendations[0] if recommendations else None)
    headline = (
        f"Top risk: {top['department']} ({top['label']})."
        if top else
        'No high-risk gaps detected in your access scope.'
    )
    facts = [{
        'department': row['department'],
        'severity': row['severity'],
        'compliance': f"{row['compliance']}%",
        'recommendation': row['recommendation'],
    } for row in recommendations]
    return {'intent': 'risks', 'headline': headline, 'facts': facts, 'sources': []}


def _intent_departments(user, question):
    rows = departments(user)
    headline = f'{len(rows)} department(s) in scope; the lowest is {min(rows, key=lambda row: row["compliance"])["name"]} at {min(rows, key=lambda row: row["compliance"])["compliance"]}% compliance.' if rows else 'No department data in scope.'
    facts = [{
        'department': row['name'],
        'compliance': f"{row['compliance']}%",
        'status': row['status'],
    } for row in rows]
    return {'intent': 'departments', 'headline': headline, 'facts': facts, 'sources': []}


def _intent_areas(user, question):
    data = summary(user)
    level = AccreditationLevel.objects.filter(cycle=AccreditationCycle.objects.filter(is_active=True).first()).filter(code='I').first()
    headlines = [
        f"Overall readiness is {data['readiness']}% ({data['completed']} of {data['total']} visible item(s) complied or closed).",
        f"{data['pending']} item(s) are in review and {data['revisions']} need revision.",
    ]
    facts = []
    if level:
        submissions = accessible_submissions(user)
        for area in level.areas.all():
            required = EvidenceRequirement.objects.filter(area=area).count()
            done = submissions.filter(requirement__area=area, status__in=COMPLETED_STATUSES).count()
            rate = round(done * 100 / required) if required else 0
            facts.append({'area': area.name, 'coverage': f'{rate}%', 'done': done, 'required': required})
    return {'intent': 'readiness', 'headline': ' '.join(headlines), 'facts': facts, 'sources': []}


def _intent_summary(user, question):
    data = summary(user)
    headline = (
        f"Across your scope: {data['readiness']}% readiness, {data['total']} visible submission(s), "
        f"{data['pending']} in review, {data['revisions']} needing revision, {data['drafts']} still drafts."
    )
    facts = [{'area': 'Readiness', 'value': f"{data['readiness']}%"}, {'area': 'In Review', 'value': data['pending']},
             {'area': 'Needs Revision', 'value': data['revisions']}, {'area': 'Drafts', 'value': data['drafts']}]
    return {'intent': 'summary', 'headline': headline, 'facts': facts, 'sources': []}


def generate_answer(user, question):
    """Return a dict with the grounded answer, mode, and source links."""
    retrieval = retrieve(user, question)
    engine_answer = compose_answer(retrieval)
    if settings.AI_ENABLED:
        try:
            llm_answer = provider_complete(build_system_prompt(retrieval), question)
            return {'answer': llm_answer, 'mode': 'llm', 'intent': retrieval['intent'], 'sources': retrieval['sources']}
        except Exception as exc:  # provider failure must never break the portal
            logger.warning('AI provider unavailable, falling back to local engine: %s', exc)
    return {'answer': engine_answer, 'mode': 'engine', 'intent': retrieval['intent'], 'sources': retrieval['sources']}


def compose_answer(retrieval):
    lines = [retrieval['headline']]
    for fact in retrieval['facts']:
        if 'code' in fact:
            lines.append(f"- {fact.get('code')} · {fact.get('title', '')} · {fact.get('department', '')} · {fact.get('status', '')}".rstrip(' ·'))
        else:
            lines.append(f"- {fact.get('department') or fact.get('area')}: {fact.get('compliance') or fact.get('value') or fact.get('recommendation', '')}")
    return '\n'.join(lines)


def build_system_prompt(retrieval):
    facts = json.dumps(retrieval['facts'], ensure_ascii=False)
    return (
        f'{AVA_PERSONA} '
        f'Facts: {facts}'
    )


def provider_complete(system_prompt, question):
    """Call an OpenAI-compatible /chat/completions endpoint."""
    url = f"{settings.AI_BASE_URL}/chat/completions"
    payload = {
        'model': settings.AI_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question},
        ],
        'temperature': 0.2,
        'max_tokens': settings.AI_MAX_TOKENS,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.AI_API_KEY}',
        },
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=settings.AI_TIMEOUT) as response:  # nosec B310 - endpoint is server-configured via AI_BASE_URL env, never from user input; timeout enforced
        data = json.loads(response.read().decode('utf-8'))
    return (data.get('choices') or [{}])[0].get('message', {}).get('content', '').strip()


def trend_labels():
    """Real date-range label for the trends panel."""
    def day(d):
        return str(d.day)
    today = timezone.localdate()
    start = today - timedelta(days=42)
    return f'{start.strftime("%b")} {day(start)} - {today.strftime("%b")} {day(today)}, {today.year}'


def trend_takeaway(weekly_submissions, weekly_revisions):
    """Human takeaway sentence derived from the real trend data."""
    if len(weekly_submissions) < 2:
        return 'Not enough history to determine a trend yet.'
    recent_sub = weekly_submissions[-1]
    previous_sub = weekly_submissions[-2]
    revision_recent = weekly_revisions[-1]
    if recent_sub > previous_sub:
        direction = f'Submission activity rose from {previous_sub} to {recent_sub} in the latest week.'
    elif recent_sub < previous_sub:
        direction = f'Submission activity fell from {previous_sub} to {recent_sub} in the latest week.'
    else:
        direction = f'Submission activity held steady at {recent_sub} in the latest week.'
    return f'{direction} {revision_recent} item(s) were sent back for revision in the latest week.'


def build_export_report(user):
    """Plain-text monitor report for the Export button."""
    data = summary(user)
    lines = [
        'JMCFI Accreditation Management System - Monitoring Report',
        f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M UTC")}',
        f'Generated by: {user.get_full_name() or user.username}',
        '',
        'HEADLINE METRICS',
        f"- Readiness: {data['readiness']}% ({data['completed']}/{data['total']})",
        f"- Compliance: {data['compliance']}%",
        f"- In review: {data['pending']}",
        f"- Needs revision: {data['revisions']}",
        f"- Drafts / not yet submitted: {data['drafts']}",
        '',
        'COMPLIANCE BY DEPARTMENT',
    ]
    for row in departments(user):
        lines.append(f"- {row['name']}: {row['compliance']}% ({row['status']})")
    lines.append('')
    lines.append('AVA ADVISORY - RISKS & RECOMMENDATIONS')
    for row in risk_recommendations(user)[:6]:
        lines.append(f"- {row['severity']}: {row['recommendation']}")
    lines.append('')
    lines.append('Generated by AVA, the JMCFI accreditation virtual assistant, from live accreditation data. Advisory only.')
    return '\n'.join(lines)
