from django.urls import path

from . import views

urlpatterns = [
    path('demandes-contact', views.DemandeContactListCreateView.as_view()),
    path('demandes-contact/<int:pk>', views.DemandeContactReponseView.as_view()),
]
