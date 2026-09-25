"""Endpoints internes appelés par n8n (automatisation), jamais par le front-end.

Protégés par un secret partagé (N8N_API_KEY, dans .env) envoyé dans l'en-tête
X-Cle-Interne : ni un compte utilisateur, ni un jeton JWT, seulement une
clé que l'équipe génère elle-même (aucun service externe impliqué).
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.models import Administrateur, Utilisateur
from apps.suivi.models import SuiviHumeur

from .models import NotificationEmail
from .services import notifier


class EstAutomatisation(BasePermission):
    message = "Accès réservé à l'automatisation (clé interne manquante ou invalide)."

    def has_permission(self, request, view):
        cle = getattr(settings, 'N8N_API_KEY', '')
        return bool(cle) and request.headers.get('X-Cle-Interne') == cle


class UtilisateursInactifsView(APIView):
    """GET /api/interne/utilisateurs-inactifs?jours=3

    Utilisateurs sans entrée de journal depuis N jours et n'ayant pas déjà
    reçu de rappel d'inactivité sur cette période (évite de relancer chaque jour).
    """

    permission_classes = [EstAutomatisation]

    def get(self, request):
        jours = int(request.query_params.get('jours', 3))
        limite = timezone.localdate() - timedelta(days=jours)
        limite_datetime = timezone.now() - timedelta(days=jours)

        recents = SuiviHumeur.objects.filter(date__gt=limite).values_list('utilisateur_id', flat=True)
        deja_relances = NotificationEmail.objects.filter(
            objet=OBJET_RAPPEL, date_envoi__gt=limite_datetime
        ).values_list('destinataire_id', flat=True)

        inactifs = (
            Utilisateur.objects.filter(date_creation__lt=limite_datetime)
            .exclude(pk__in=recents)
            .exclude(pk__in=deja_relances)
        )
        return Response([{'id': u.pk, 'prenom': u.prenom, 'email': u.email} for u in inactifs])


OBJET_RAPPEL = 'Un moment pour prendre soin de vous'


class AdministrateursView(APIView):
    """GET /api/interne/administrateurs"""

    permission_classes = [EstAutomatisation]

    def get(self, request):
        return Response([{'id': a.pk, 'email': a.email} for a in Administrateur.objects.all()])


class NotificationInterneSerializer(serializers.Serializer):
    destinataire_id = serializers.IntegerField()
    objet = serializers.CharField(max_length=200)
    contenu = serializers.CharField()
    # Clé de préférence (ex. « nouvelle_demande ») : si le destinataire a
    # désactivé ce type de notification, rien n'est créé.
    preference = serializers.CharField(max_length=50, required=False)


class CreerNotificationView(APIView):
    """POST /api/interne/notifications-email — crée une NotificationEmail."""

    permission_classes = [EstAutomatisation]

    def post(self, request):
        serializer = NotificationInterneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donnees = serializer.validated_data
        from apps.comptes.models import CompteUtilisateur

        try:
            compte = CompteUtilisateur.objects.get(pk=donnees['destinataire_id'])
        except CompteUtilisateur.DoesNotExist:
            return Response({'detail': 'Destinataire introuvable.'}, status=404)
        preference = donnees.get('preference')
        if preference and not compte.preferences.get(preference, {}).get('email', True):
            return Response({'ignoree': True, 'raison': 'Notification désactivée par le destinataire.'})
        notification = notifier(compte, donnees['objet'], donnees['contenu'])
        return Response({'id': notification.pk}, status=201)
