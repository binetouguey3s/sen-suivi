"""Vues de comptes : inscription, connexion, validation des professionnels.

Vues basées sur les classes uniquement : vues
génériques DRF, jamais de @api_view.
"""

from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Professionnel
from .permissions import EstAdministrateur
from .services import confirmer_reinitialisation, demander_reinitialisation
from .serializers import (
    ConfirmationReinitialisationSerializer,
    DemandeReinitialisationSerializer,
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


class DemandeReinitialisationView(APIView):
    """POST /api/auth/mot-de-passe-oublie — répond toujours 200 (pas de fuite d'existence du compte)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DemandeReinitialisationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        demander_reinitialisation(serializer.validated_data['email'])
        return Response({'detail': 'Si ce compte existe, un lien vient de lui être envoyé.'})


class ConfirmationReinitialisationView(APIView):
    """POST /api/auth/mot-de-passe-oublie/confirmer"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmationReinitialisationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not confirmer_reinitialisation(**serializer.validated_data):
            raise serializers.ValidationError('Ce lien est invalide ou a expiré.')
        return Response({'detail': 'Votre mot de passe a été modifié.'}, status=status.HTTP_200_OK)
