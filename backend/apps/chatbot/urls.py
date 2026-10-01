from django.urls import path

from . import views

urlpatterns = [
    path('chatbot/message', views.ChatbotMessageView.as_view()),
    path('chatbot/message-vocal', views.ChatbotVocalView.as_view()),
    path('chatbot/reponse-vocale', views.ReponseVocaleView.as_view()),
    path('chatbot/conversations', views.ConversationsView.as_view()),
    path('chatbot/conversations/<int:pk>', views.ConversationDetailView.as_view()),
]
