from django.urls import path

from . import views

app_name = 'resources'

urlpatterns = [
    path('documents/', views.DocumentRepositoryView.as_view(), name='document_repository'),
    path('communication/', views.CommunicationView.as_view(), name='communication'),
    path('communication/messages/', views.MessagesApiView.as_view(), name='messages_api'),
    path('communication/read/', views.MarkConversationReadView.as_view(), name='messages_read'),
]
