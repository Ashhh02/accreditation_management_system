from django.views.generic import TemplateView

from .charting import build_line_chart


class DashboardView(TemplateView):
    """
    Main QA Office dashboard: KPI summary, AI readiness alert,
    submission trend, and per-area readiness.

    All data below is placeholder UI data. Once submissions/areas
    have real models, replace each block with a queryset/service call
    and keep the template untouched.
    """
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['cycle'] = {
            'office': 'Quality Assurance Office',
            'academic_year': '2025–2026',
            'program': 'PACUCOA Accreditation Cycle',
        }

        context['alert'] = {
            'area_code': 'Area VIII',
            'area_name': 'SOCE',
            'readiness_gap': 45,
            'days_left': 20,
            'departments_missing': 3,
            'message': (
                'has a 45% readiness gap with 20 days until the preliminary '
                'deadline. 3 departments are missing critical supporting '
                'documents. Immediate action recommended.'
            ),
        }

        context['stats'] = [
            {
                'label': 'Total Submissions',
                'value': 247,
                'note': '+18 this week',
                'icon': 'file',
                'tone': 'rose',
            },
            {
                'label': 'Complied',
                'value': 182,
                'note': '73.7% compliance rate',
                'icon': 'check',
                'tone': 'green',
            },
            {
                'label': 'Pending Review',
                'value': 41,
                'note': '12 overdue',
                'icon': 'clock',
                'tone': 'gold',
            },
            {
                'label': 'Needs Revision',
                'value': 24,
                'note': '8 critical',
                'icon': 'alert',
                'tone': 'red',
            },
        ]

        months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
        raw_series = [
            {'name': 'Submitted', 'color': 'maroon', 'values': [12, 21, 29, 37, 44, 52]},
            {'name': 'Complied', 'color': 'green', 'values': [8, 16, 24, 32, 39, 47]},
            {'name': 'Revision', 'color': 'gold', 'values': [2, 3, 3, 4, 4, 5]},
        ]
        context['trend'] = {
            'range_label': 'Feb – Jul 2026',
            'y_ticks': [0, 15, 30, 45, 60],
            'chart': build_line_chart(months, raw_series, max_value=60),
        }

        context['area_readiness'] = {
            'sublabel': 'Level I · All departments avg.',
            'areas': [
                {'code': 'Area I', 'value': 92, 'tone': 'gold'},
                {'code': 'Area III', 'value': 88, 'tone': 'green'},
                {'code': 'Area V', 'value': 79, 'tone': 'gold'},
                {'code': 'Area VII', 'value': 31, 'tone': 'maroon'},
                {'code': 'Area IX', 'value': 84, 'tone': 'green'},
                {'code': 'Area XI', 'value': 68, 'tone': 'gold'},
            ],
        }

        return context
