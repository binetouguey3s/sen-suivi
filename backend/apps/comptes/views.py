"""Vues de comptes : inscription, connexion, validation des professionnels.

Vues basées sur les classes uniquement (CLAUDE.md section 7) : vues
génériques DRF, jamais de @api_view.
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Professionnel
from .permissions import EstAdministrateur
from .serializers import (
    InscriptionProfessionnelSerializer,
    InscriptionUtilisateurSerializer,
    LoginSerializer,
    ProfessionnelLectureSerializer,
    ProfessionnelValidationSerializer,
)


class InscriptionUtilisateurView(generics.CreateAPIView):
    """POST /api/auth/register"""

    permission_classes = [AllowAny]
    serializer_class = InscriptionUtilisateurSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login — refuse un professionnel dont le compte n'est pas VALIDE."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class InscriptionProfessionnelView(generics.CreateAPIView):
    """POST /api/professionnels/inscription — crée le compte en EN_ATTENTE."""

    permission_classes = [AllowAny]
    serializer_class = InscriptionProfessionnelSerializer


class ProfessionnelListView(generics.ListAPIView):
    """GET /api/professionnels?statut=EN_ATTENTE — réservé aux administrateurs."""

    permission_classes = [EstAdministrateur]
    serializer_class = ProfessionnelLectureSerializer

    def get_queryset(self):
        queryset = Professionnel.objects.all()
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut_validation=statut)
        return queryset


class ProfessionnelValidationView(generics.UpdateAPIView):
    """PATCH /api/professionnels/{id} — passe le compte à VALIDE ou REFUSE."""

    permission_classes = [EstAdministrateur]
    serializer_class = ProfessionnelValidationSerializer
    queryset = Professionnel.objects.all()
    http_method_names = ['patch']
