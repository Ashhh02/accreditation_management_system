from django.views.generic import TemplateView


class DocumentRepositoryView(TemplateView):
    template_name = 'resources/document_repository.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departments = [
            {'label': 'All Documents', 'active': True},
            {'label': 'College of Engineering', 'active': False},
            {'label': 'College of Nursing', 'active': False},
            {'label': 'College of Business', 'active': False},
            {'label': 'Library', 'active': False},
            {'label': 'Student Affairs', 'active': False},
            {'label': 'Facilities Office', 'active': False},
        ]
        documents = [
            {
                'name': 'Faculty_Credentials_2025-2026.pdf',
                'department': 'College of Engineering',
                'details': 'Area II · Level I · Prof. J. Reyes · 3.2 MB',
                'tags': ['Faculty', 'Credentials'],
                'version': 'v4',
                'updated': 'Updated Jul 14, 2026',
                'status': 'Approved',
                'tone': 'green',
                'icon_tone': 'rose',
            },
            {
                'name': 'Research_Output_Compilation_Q1.xlsx',
                'department': 'College of Nursing',
                'details': 'Area V · Level I · Dr. C. Bautista · 1.8 MB',
                'tags': ['Research', 'Output'],
                'version': 'v2',
                'updated': 'Updated Jul 13, 2026',
                'status': 'Pending',
                'tone': 'gold',
                'icon_tone': 'green',
            },
            {
                'name': 'Student_Handbook_AY2025.pdf',
                'department': 'Student Affairs',
                'details': 'Area VII · Level I · Ms. F. Santos · 5.4 MB',
                'tags': ['Students', 'Policy'],
                'version': 'v1',
                'updated': 'Updated Jul 12, 2026',
                'status': 'Approved',
                'tone': 'green',
                'icon_tone': 'rose',
            },
            {
                'name': 'Library_Collection_Inventory.docx',
                'department': 'Library',
                'details': 'Area VI · Level I · Ms. A. Cruz · 2.1 MB',
                'tags': ['Library', 'Inventory'],
                'version': 'v3',
                'updated': 'Updated Jul 11, 2026',
                'status': 'Needs Revision',
                'tone': 'rose',
                'icon_tone': 'blue',
            },
            {
                'name': 'Physical_Plant_Assessment_2026.pdf',
                'department': 'Facilities Office',
                'details': 'Area IX · Level I · Engr. B. Ramos · 8.7 MB',
                'tags': ['Facilities', 'Assessment'],
                'version': 'v2',
                'updated': 'Updated Jul 10, 2026',
                'status': 'Approved',
                'tone': 'green',
                'icon_tone': 'rose',
            },
            {
                'name': 'Organizational_Chart_2025.pdf',
                'department': 'Registrar',
                'details': 'Area X · Level I · Admin. T. Magtibay · 0.9 MB',
                'tags': ['Organization', 'Structure'],
                'version': 'v1',
                'updated': 'Updated Jul 9, 2026',
                'status': 'Pending',
                'tone': 'gold',
                'icon_tone': 'rose',
            },
        ]
        context.update(
            {
                'page_title': 'Document Repository',
                'departments': departments,
                'documents': documents,
                'repo_stats': [
                    {'label': 'Total Documents', 'value': 6, 'tone': 'rose'},
                    {'label': 'Approved', 'value': 3, 'tone': 'green'},
                    {'label': 'Pending / Revision', 'value': 3, 'tone': 'rose'},
                ],
            }
        )
        return context


class CommunicationView(TemplateView):
    template_name = 'resources/communication.html'
    extra_context = {'page_title': 'Communication'}
