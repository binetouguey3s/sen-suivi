"""Endpoints internes appelés par n8n (automatisation), jamais par le front-end.

Protégés par un secret partagé (N8N_API_KEY, dans .env) envoyé dans l'en-tête
X-Cle-Interne : ni un compte utilisateur, ni un jeton JWT, seulement une
clé que l'équipe génère elle-même (aucun service externe impliqué).
"""

from datetime import timedelta

from django.conf import settings
from django.db.models import Max
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


# Textes des rappels : doux, jamais culpabilisants, toujours facultatifs
OBJET_RAPPEL = 'Un moment pour prendre soin de vous'
CONTENU_RAPPEL = (
    "Bonjour {prenom}, si vous en avez envie, quelques secondes suffisent pour noter votre humeur "
    "du jour dans Sen Suivi. Aucune obligation : votre journal vous attend quand vous le souhaitez. "
    "Sen Suivi ne remplace pas un professionnel de santé."
)
OBJET_RAPPEL_TEST = 'Faire le point, si vous le souhaitez'
CONTENU_RAPPEL_TEST = (
    "Bonjour {prenom}, votre dernière auto-évaluation date d'il y a plus d'un mois. Si vous en avez "
    "envie, la refaire vous permet de voir comment les choses ont évolué pour vous. "
    "Sen Suivi ne remplace pas un professionnel de santé."
)


def _deja_relances():
    """Utilisateurs relancés (journal ou test) pendant la fréquence maximale :
    jamais plus d'un rappel par période, tous types confondus."""
    depuis = timezone.now() - timedelta(days=settings.RAPPEL_FREQUENCE_MAX_JOURS)
    return NotificationEmail.objects.filter(
        objet__in=[OBJET_RAPPEL, OBJET_RAPPEL_TEST], date_envoi__gt=depuis
    ).values_list('destinataire_id', flat=True)


def _accepte(compte, preference):
    """Rappel activé par défaut, désactivable dans les paramètres."""
    return (compte.preferences or {}).get(preference, {}).get('email', True)


def _rappels(utilisateurs, objet, contenu, preference):
    return [
        {
            'id': u.pk,
            'prenom': u.prenom,
            'objet': objet,
            'contenu': contenu.format(prenom=u.prenom),
            'preference': preference,
        }
        for u in utilisateurs
        if _accepte(u, preference)
    ]


class UtilisateursInactifsView(APIView):
    """GET /api/interne/utilisateurs-inactifs

    Utilisateurs sans entrée de journal depuis RAPPEL_JOURNAL_JOURS, qui n'ont
    pas désactivé ce rappel et n'ont reçu aucun rappel pendant la fréquence
    maximale (RAPPEL_FREQUENCE_MAX_JOURS). Réglages lus depuis le .env.
    """

    permission_classes = [EstAutomatisation]

    def get(self, request):
        jours = settings.RAPPEL_JOURNAL_JOURS
        limite = timezone.localdate() - timedelta(days=jours)
        limite_datetime = timezone.now() - timedelta(days=jours)

        recents = SuiviHumeur.objects.filter(date__gt=limite).values_list('utilisateur_id', flat=True)
        inactifs = (
            Utilisateur.objects.filter(date_creation__lt=limite_datetime)
            .exclude(pk__in=recents)
            .exclude(pk__in=_deja_relances())
        )
        return Response(_rappels(inactifs, OBJET_RAPPEL, CONTENU_RAPPEL, 'rappel_journal'))


class UtilisateursARetesterView(APIView):
    """GET /api/interne/utilisateurs-a-retester

    Utilisateurs dont la dernière auto-évaluation date de plus de
    RAPPEL_TEST_JOURS : on leur propose, sans insister, de la refaire.
    """

    permission_classes = [EstAutomatisation]

    def get(self, request):
        limite = timezone.now() - timedelta(days=settings.RAPPEL_TEST_JOURS)
        a_retester = (
            Utilisateur.objects.annotate(dernier_test=Max('auto_evaluations__date'))
            .filter(dernier_test__lt=limite)
            .exclude(pk__in=_deja_relances())
        )
        return Response(_rappels(a_retester, OBJET_RAPPEL_TEST, CONTENU_RAPPEL_TEST, 'rappel_auto_evaluation'))


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
        notification = notifier(compte, donnees['objet'], donnees['contenu'], preference)
        return Response({'id': notification.pk}, status=201)
