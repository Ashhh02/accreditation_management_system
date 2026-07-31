from django.views.generic import TemplateView


class ReportsMonitoringView(TemplateView):
    template_name = 'intelligence/reports_monitoring.html'
    extra_context = {'page_title': 'Reports & Monitoring'}


class SmartCompanionView(TemplateView):
    template_name = 'intelligence/smart_companion.html'
    extra_context = {'page_title': 'Smart Companion'}
