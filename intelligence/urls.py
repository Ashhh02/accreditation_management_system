from django.urls import path

from . import views

app_name = 'intelligence'

urlpatterns = [
    path('reports/', views.ReportsMonitoringView.as_view(), name='reports_monitoring'),
    path('reports/export/', views.ExportReportView.as_view(), name='export_report'),
    path('ai-insights/', views.AiInsightsView.as_view(), name='ai_insights'),
    path('smart-companion/', views.SmartCompanionView.as_view(), name='smart_companion'),
    path('smart-companion/ask/', views.CompanionAskView.as_view(), name='companion_ask'),
]
