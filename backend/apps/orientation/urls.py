from django.urls import path

from . import views

urlpatterns = [
    path('orientation/suggestion', views.SuggestionView.as_view()),
    path('acces/etat', views.EtatAccesView.as_view()),
    path('acces/paiement', views.PaiementView.as_view()),
]
