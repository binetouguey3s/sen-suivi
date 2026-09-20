from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('auth/register', views.InscriptionUtilisateurView.as_view()),
    path('auth/login', views.LoginView.as_view()),
    path('auth/refresh', TokenRefreshView.as_view()),
    path('auth/mot-de-passe-oublie', views.DemandeReinitialisationView.as_view()),
    path('auth/mot-de-passe-oublie/confirmer', views.ConfirmationReinitialisationView.as_view()),
    path('comptes/moi', views.CompteMoiView.as_view()),
    path('comptes/moi/mot-de-passe', views.ChangementMotDePasseView.as_view()),
    path('professionnels/inscription', views.InscriptionProfessionnelView.as_view()),
    path('professionnels/valides', views.ProfessionnelPublicListView.as_view()),
    path('professionnels', views.ProfessionnelListView.as_view()),
    path('professionnels/<int:pk>', views.ProfessionnelDetailView.as_view()),
]
