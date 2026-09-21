"""Vues de comptes : inscription, connexion, validation des professionnels.

Vues basées sur les classes uniquement : vues
génériques DRF, jamais de @api_view.
"""

from django.db.models import Q
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.notifications.services import declencher_workflow

from .models import Professionnel, StatutValidationPro
from .permissions import EstAdministrateur
from .services import confirmer_reinitialisation, demander_reinitialisation
from .serializers import (
    ChangementMotDePasseSerializer,
    CompteMoiSerializer,
    ConfirmationReinitialisationSerializer,
    SuppressionCompteSerializer,
    DemandeReinitialisationSerializer,
    InscriptionProfessionnelSerializer,
    InscriptionUtilisateurSerializer,
    LoginSerializer,
    ProfessionnelLectureSerializer,
    ProfessionnelPublicSerializer,
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

    def perform_create(self, serializer):
        professionnel = serializer.save()
        # Prévient les administrateurs via le workflow n8n (best-effort)
        declencher_workflow(
            'nouveau-professionnel',
            {'nom': professionnel.nom, 'specialite': professionnel.get_specialite_display(), 'ville': professionnel.ville},
        )


class ProfessionnelListView(generics.ListAPIView):
    """GET /api/professionnels?statut=EN_ATTENTE&q=texte — réservé aux administrateurs."""

    permission_classes = [EstAdministrateur]
    serializer_class = ProfessionnelLectureSerializer

    def get_queryset(self):
        queryset = Professionnel.objects.all()
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut_validation=statut)
        recherche = self.request.query_params.get('q')
        if recherche:
            queryset = queryset.filter(
                Q(nom__icontains=recherche) | Q(email__icontains=recherche) | Q(ville__icontains=recherche)
            )
        return queryset


class ProfessionnelDetailView(generics.RetrieveUpdateAPIView):
    """GET /api/professionnels/{id} — profil d'un professionnel validé (compte connecté) ;
    PATCH — un administrateur passe le compte à VALIDE ou REFUSE."""

    http_method_names = ['get', 'patch']

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [EstAdministrateur()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ProfessionnelValidationSerializer
        return ProfessionnelPublicSerializer

    def get_queryset(self):
        if self.request.method == 'PATCH':
            return Professionnel.objects.all()
        return Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE)


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


class ProfessionnelPublicListView(generics.ListAPIView):
    """GET /api/professionnels/valides — profils validés uniquement, accès public."""

    permission_classes = [AllowAny]
    serializer_class = ProfessionnelPublicSerializer

    def get_queryset(self):
        return Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE)


class CompteMoiView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH /api/comptes/moi ; DELETE avec confirmation par mot de passe."""

    permission_classes = [IsAuthenticated]
    serializer_class = CompteMoiSerializer
    http_method_names = ['get', 'patch', 'delete']

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        serializer = SuppressionCompteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VueEnsembleAdminView(APIView):
    """GET /api/administration/vue-ensemble — actions en attente pour l'administrateur.

    Volontairement dépourvue de tout chiffre d'usage ou de performance
 : uniquement les actions réelles qui attendent une
    décision, comptées dans la base, jamais une tendance ou un pourcentage.
    """

    permission_classes = [EstAdministrateur]

    def get(self, request):
        from apps.forum.models import CommentaireForum, PublicationForum
        from apps.forum.models import StatutModeration as StatutModerationForum

        return Response(
            {
                'professionnels_en_attente': Professionnel.objects.filter(
                    statut_validation=StatutValidationPro.EN_ATTENTE
                ).count(),
                'publications_en_attente': PublicationForum.objects.filter(
                    statut_moderation=StatutModerationForum.EN_ATTENTE
                ).count(),
                'commentaires_en_attente': CommentaireForum.objects.filter(
                    statut_moderation=StatutModerationForum.EN_ATTENTE
                ).count(),
            }
        )


class ChangementMotDePasseView(APIView):
    """POST /api/comptes/moi/mot-de-passe"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangementMotDePasseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['nouveau'])
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Votre mot de passe a été modifié.'})
