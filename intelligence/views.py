from django.views.generic import TemplateView


class ReportsMonitoringView(TemplateView):
    template_name = 'intelligence/reports_monitoring.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'page_title': 'Reports & Monitoring',
                'insights': [
                    {
                        'message': 'Area VIII (SOCE) is the most critical gap - 45% readiness with 20 days to deadline. Immediate document uploads required.',
                        'tone': 'rose',
                        'icon': 'alert',
                    },
                    {
                        'message': 'Revision rate has decreased 75% over 6 weeks, indicating improving submission quality across departments.',
                        'tone': 'green',
                        'icon': 'trend-up',
                    },
                    {
                        'message': 'College of Arts & Sciences has the lowest compliance rate (65%). 3 areas still have zero submissions.',
                        'tone': 'rose',
                        'icon': 'alert',
                    },
                    {
                        'message': 'Recommend deploying Area Chair to College of Engineering for Areas IV and VII before July 20 deadline.',
                        'tone': 'gold',
                        'icon': 'alert',
                    },
                ],
                'kpis': [
                    {'value': '74.3%', 'label': 'Overall Readiness', 'delta': '+5.2%', 'tone': 'green'},
                    {'value': '247', 'label': 'Total Submissions', 'delta': '+18 this week', 'tone': 'green'},
                    {'value': '73.7%', 'label': 'Compliance Rate', 'delta': '+3.1%', 'tone': 'green'},
                    {'value': '12', 'label': 'Overdue Items', 'delta': '-4 from last week', 'tone': 'rose'},
                ],
                'departments': [
                    {
                        'name': 'Engineering',
                        'submitted': 42,
                        'compiled': 33,
                        'compliance': 78,
                        'status': 'At Risk',
                        'tone': 'gold',
                    },
                    {
                        'name': 'Business',
                        'submitted': 38,
                        'compiled': 32,
                        'compliance': 85,
                        'status': 'On Track',
                        'tone': 'green',
                    },
                    {
                        'name': 'Education',
                        'submitted': 35,
                        'compiled': 25,
                        'compliance': 72,
                        'status': 'At Risk',
                        'tone': 'gold',
                    },
                    {
                        'name': 'Nursing',
                        'submitted': 44,
                        'compiled': 40,
                        'compliance': 91,
                        'status': 'On Track',
                        'tone': 'green',
                    },
                    {
                        'name': 'Arts & Sci',
                        'submitted': 31,
                        'compiled': 20,
                        'compliance': 65,
                        'status': 'Critical',
                        'tone': 'rose',
                    },
                ],
                'radar_points': '145,20 198,48 225,94 202,148 170,188 112,205 78,158 32,138 42,84 92,56',
                'trend_approval_points': '30,220 120,182 210,158 300,132 390,92 480,48',
                'trend_revision_points': '30,152 120,170 210,188 300,202 390,210 480,218',
            }
        )
        return context


class SmartCompanionView(TemplateView):
    template_name = 'intelligence/smart_companion.html'
    extra_context = {'page_title': 'Smart Companion'}
