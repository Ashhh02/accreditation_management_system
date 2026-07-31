from django.views.generic import TemplateView


class DocumentRepositoryView(TemplateView):
    template_name = 'resources/document_repository.html'
    extra_context = {'page_title': 'Document Repository'}


class CommunicationView(TemplateView):
    template_name = 'resources/communication.html'
    extra_context = {'page_title': 'Communication'}
