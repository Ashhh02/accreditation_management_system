import math
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accreditation.models import AccreditationCycle, AccreditationLevel, EvidenceRequirement
from core.access import accessible_submissions
from core.mixins import ApprovedUserRequiredMixin
from core.ratelimit import hit_rate_limit

from . import services
from .services import COMPLETED_STATUSES


def _points(values, max_value=36):
    x_values = [30, 120, 210, 300, 390, 480]
    return ' '.join(f'{x},{220 - round(min(value, max_value) / max_value * 172)}' for x, value in zip(x_values, values))


class ReportsMonitoringView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'intelligence/reports_monitoring.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cycle = AccreditationCycle.objects.filter(is_active=True).first()
        submissions = accessible_submissions(user)
        data = services.summary(user)
        readiness, compliance, pending, revisions, total, completed = (
            data['readiness'],
            data['compliance'],
            data['pending'],
            data['revisions'],
            data['total'],
            data['completed'],
        )

        level = AccreditationLevel.objects.filter(cycle=cycle).filter(code='I').first() if cycle else None
        radar_values = []
        if level:
            for area in level.areas.all():
                required = EvidenceRequirement.objects.filter(area=area).count()
                done = submissions.filter(requirement__area=area, status__in=COMPLETED_STATUSES).count()
                radar_values.append(round(done * 100 / required) if required else 0)
        radar_values = (radar_values + [0] * 11)[:11]
        radar_points = ' '.join(
            f'{130 + round(105 * value / 100 * math.cos(2 * math.pi * index / 11 - math.pi / 2)):.0f},{125 + round(105 * value / 100 * math.sin(2 * math.pi * index / 11 - math.pi / 2)):.0f}'
            for index, value in enumerate(radar_values)
        )

        recent = timezone.now()
        weekly_submitted = []
        weekly_revisions = []
        for week in range(6, 0, -1):
            start = recent - timedelta(days=week * 7)
            end = start + timedelta(days=7)
            weekly_submitted.append(submissions.filter(created_at__gte=start, created_at__lt=end).count())
            weekly_revisions.append(submissions.filter(
                reviews__created_at__gte=start,
                reviews__created_at__lt=end,
                reviews__decision='REQUEST_REVISION',
            ).distinct().count())

        risk_rows = services.risk_recommendations(user)
        context.update({
            'page_title': 'Reports & Monitoring',
            'cycle': cycle,
            'kpis': [
                {'value': f'{readiness}%', 'label': 'Overall Readiness', 'delta': f'{total} visible submissions', 'tone': 'green' if readiness >= 80 else 'gold'},
                {'value': total, 'label': 'Total Submissions', 'delta': f'{pending} pending review', 'tone': 'green'},
                {'value': f'{compliance}%', 'label': 'Compliance Rate', 'delta': f'{completed} complied or closed', 'tone': 'green' if compliance >= 80 else 'gold'},
                {'value': revisions, 'label': 'Needs Revision', 'delta': 'Returned for correction', 'tone': 'rose' if revisions else 'green'},
            ],
            'departments': services.departments(user),
            'risk_items': risk_rows,
            'radar_points': radar_points,
            'trend_approval_points': _points(weekly_submitted),
            'trend_revision_points': _points(weekly_revisions),
            'trend_range_label': services.trend_labels(),
            'trend_takeaway': services.trend_takeaway(user, weekly_submitted, weekly_revisions),
        })
        return context


class SmartCompanionView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'intelligence/smart_companion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = services.summary(self.request.user)
        mode = 'AVA is connected to an AI provider for grounded answers.' if settings.AI_ENABLED else 'AVA answers are generated from the live database.'
        context.update({
            'page_title': 'AVA Assistant',
            'companion_mode': mode,
            'summary': data,
            'companion_insights': [
                {
                    'title': 'Revision Queue',
                    'description': f'{data["revisions"]} visible evidence items need correction.',
                    'tone': 'rose' if data['revisions'] else 'green',
                },
                {
                    'title': 'Pending Review',
                    'description': f'{data["pending"]} items are moving through internal review.',
                    'tone': 'gold',
                },
                {
                    'title': 'Overall Readiness',
                    'description': f'{data["readiness"]}% of visible evidence is complied or closed.',
                    'tone': 'green' if data['readiness'] >= 80 else 'gold',
                },
            ],
            'sample_prompts': [
                {
                    'title': 'Evidence Help',
                    'description': 'Find missing files and weak submissions.',
                    'prompts': [
                        'Which evidence needs revision?',
                        'Which documents are missing?',
                        'Check the next review stage.',
                        'Which deadlines are approaching?',
                    ],
                },
                {
                    'title': 'Readiness Review',
                    'description': 'Summarize current gaps.',
                    'prompts': [
                        'Summarize visible readiness.',
                        'Show pending reviewer work.',
                        'Show complied evidence.',
                        'Which departments are at risk?',
                    ],
                },
            ],
        })
        return context


class AiInsightsView(ApprovedUserRequiredMixin, TemplateView):
    template_name = 'intelligence/ai_insights.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = services.ai_insights(self.request.user)
        context.update({
            'page_title': 'AI Insights',
            'insights': data['insights'],
            'assessment': data['assessment'],
            'area_readiness': data['areas'],
            'top_risk': data['top_risk'],
            'risk_items': data['risks'],
            'summary': data['summary'],
            'companion_mode': 'AVA assessments are grounded in live accreditation data.',
        })
        return context


class CompanionAskView(ApprovedUserRequiredMixin, View):
    """POST /smart-companion/ask  ->  grounded answer as JSON."""

    def post(self, request, *args, **kwargs):
        question = (request.POST.get('question') or '').strip()
        if not question:
            return JsonResponse({'error': 'Ask a question.'}, status=400)
        rate = getattr(settings, 'RATE_LIMIT_COMPANION', {'limit': 30, 'window': 300})
        if hit_rate_limit(request, 'companion', rate['limit'], rate['window'], identity=request.user.pk):
            return JsonResponse({'error': 'Too many questions. Please wait a moment.'}, status=429)
        return JsonResponse(services.generate_answer(request.user, question))


class ExportReportView(ApprovedUserRequiredMixin, View):
    """POST /reports/export -> plain-text monitor report download."""

    def post(self, request, *args, **kwargs):
        report = services.build_export_report(request.user)
        response = HttpResponse(report, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="accreditation-report.txt"'
        return response
