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

from . import rappels
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
# Avec le consentement à la personnalisation, et une ressource qui répond à une préoccupation
CONTENU_RAPPEL_PERSONNALISE = (
    "Bonjour {prenom}, et si vous preniez 5 minutes pour vous {moment} ? Une idée : « {titre} » ({duree} min). "
    "Si vous en avez envie, vous pouvez aussi noter votre humeur du jour : aucune obligation. "
    "Sen Suivi ne remplace pas un professionnel de santé."
)
OBJET_RAPPEL_TEST = 'Faire le point, si vous le souhaitez'
CONTENU_RAPPEL_TEST = (
    "Bonjour {prenom}, votre dernière auto-évaluation date d'il y a plus d'un mois. Si vous en avez "
    "envie, la refaire vous permet de voir comment les choses ont évolué pour vous. "
    "Sen Suivi ne remplace pas un professionnel de santé."
)
CONTENU_RAPPEL_TEST_PERSONNALISE = (
    "Bonjour {prenom}, votre dernière auto-évaluation date d'il y a plus d'un mois. Si vous en avez "
    "envie, la refaire vous permet de voir comment les choses ont évolué pour vous. Et pour prendre "
    "5 minutes pour vous {moment}, une idée : « {titre} » ({duree} min). "
    "Sen Suivi ne remplace pas un professionnel de santé."
)
OBJETS_RAPPELS = [OBJET_RAPPEL, OBJET_RAPPEL_TEST]


def _envois_recents(utilisateurs) -> dict[int, list]:
    """Dates des rappels (journal ou test) reçus récemment, par personne :
    la fréquence se compte tous types confondus."""
    jours = max(settings.RAPPEL_FREQUENCE_MAX_JOURS, rappels.JOURS_SEMAINE)
    envois: dict[int, list] = {}
    for destinataire, date in NotificationEmail.objects.filter(
        destinataire_id__in=[u.pk for u in utilisateurs],
        objet__in=OBJETS_RAPPELS,
        date_envoi__gt=timezone.now() - timedelta(days=jours),
    ).values_list('destinataire_id', 'date_envoi'):
        envois.setdefault(destinataire, []).append(date)
    return envois


def _accepte(compte, preference):
    """Rappel activé par défaut, désactivable dans les paramètres."""
    return (compte.preferences or {}).get(preference, {}).get('email', True)


def _contenu(utilisateur, modele, modele_personnalise, moment):
    """Texte du rappel ; avec consentement et une ressource adaptée, il en propose une."""
    ressource = rappels.ressource_suggeree(utilisateur)
    if ressource is None:
        return modele.format(prenom=utilisateur.prenom)
    return modele_personnalise.format(
        prenom=utilisateur.prenom,
        moment=rappels.MOMENT_DANS_LA_PHRASE[moment],
        titre=ressource.titre,
        duree=ressource.duree_lecture,
    )


def _rappels(utilisateurs, objet, modeles, preference, moment, journal):
    """Rappels à envoyer, après les choix de chacun : réglage de notification,
    rappels de l'onboarding (journal seulement), moment de la journée et fréquence."""
    utilisateurs = list(utilisateurs)
    envois = _envois_recents(utilisateurs)
    choisis = [
        u for u in utilisateurs
        if _accepte(u, preference)
        and not (journal and rappels.journal_refuse(u))
        and (moment is None or moment in rappels.moments(u))
        and rappels.frequence_respectee(u, envois.get(u.pk, []))
    ]
    return [
        {
            'id': u.pk,
            'prenom': u.prenom,
            'objet': objet,
            'contenu': _contenu(u, *modeles, moment),
            'preference': preference,
        }
        for u in choisis
    ]


def _moment(request):
    """?moment=matin|midi|soir|coucher (déclencheurs n8n) ; absent : tous les moments."""
    moment = request.query_params.get('moment')
    if moment is not None and moment not in rappels.MOMENTS:
        raise serializers.ValidationError({'moment': f"Choisir parmi : {', '.join(rappels.MOMENTS)}."})
    return moment


class UtilisateursInactifsView(APIView):
    """GET /api/interne/utilisateurs-inactifs?moment=soir

    Utilisateurs sans entrée de journal depuis RAPPEL_JOURNAL_JOURS, qui n'ont
    pas désactivé ce rappel (paramètres ET onboarding), dont c'est le moment
    préféré, et dont la fréquence choisie le permet. Réglages lus depuis le .env.
    """

    permission_classes = [EstAutomatisation]

    def get(self, request):
        moment = _moment(request)
        jours = settings.RAPPEL_JOURNAL_JOURS
        limite = timezone.localdate() - timedelta(days=jours)
        limite_datetime = timezone.now() - timedelta(days=jours)

        recents = SuiviHumeur.objects.filter(date__gt=limite).values_list('utilisateur_id', flat=True)
        inactifs = Utilisateur.objects.filter(date_creation__lt=limite_datetime).exclude(pk__in=recents)
        return Response(_rappels(
            inactifs, OBJET_RAPPEL, (CONTENU_RAPPEL, CONTENU_RAPPEL_PERSONNALISE), 'rappel_journal', moment, journal=True,
        ))


class UtilisateursARetesterView(APIView):
    """GET /api/interne/utilisateurs-a-retester?moment=soir

    Utilisateurs dont la dernière auto-évaluation date de plus de
    RAPPEL_TEST_JOURS : on leur propose, sans insister, de la refaire.
    """

    permission_classes = [EstAutomatisation]

    def get(self, request):
        moment = _moment(request)
        limite = timezone.now() - timedelta(days=settings.RAPPEL_TEST_JOURS)
        a_retester = Utilisateur.objects.annotate(dernier_test=Max('auto_evaluations__date')).filter(dernier_test__lt=limite)
        return Response(_rappels(
            a_retester, OBJET_RAPPEL_TEST, (CONTENU_RAPPEL_TEST, CONTENU_RAPPEL_TEST_PERSONNALISE),
            'rappel_auto_evaluation', moment, journal=False,
        ))


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
