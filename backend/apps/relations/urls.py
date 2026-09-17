from django.urls import path

from . import views

urlpatterns = [
    path('demandes-contact', views.DemandeContactCreateView.as_view()),
]
