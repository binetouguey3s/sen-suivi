"""Signalement des situations graves à l'équipe Sen Suivi.

Chaque situation grave exprimée par un utilisateur connecté (risque vital,
détresse intense, danger pour autrui, violences subies) prévient les
administrateurs, dans la cloche et par e-mail. Ils ne reçoivent que le
pseudonyme, la nature et l'heure : jamais le contenu des messages.
"""

from datetime import timedelta

from django.utils import timezone

from apps.comptes.models import Administrateur
from apps.notifications.services import notifier

from .models import NatureRisque, SignalementRisque

# Au plus un signalement par utilisateur et par période, pour ne pas noyer l'équipe
SIGNALEMENT_INTERVALLE_HEURES = 6


def signaler_equipe(utilisateur, nature: str, personne_prevenue: str | None) -> SignalementRisque | None:
    if nature not in NatureRisque.values:
        return None
    recent = SignalementRisque.objects.filter(
        utilisateur=utilisateur, date__gte=timezone.now() - timedelta(hours=SIGNALEMENT_INTERVALLE_HEURES)
    ).exists()
    if recent:
        return None
    signalement = SignalementRisque.objects.create(
        utilisateur=utilisateur, nature=nature, personne_confiance_prevenue=bool(personne_prevenue)
    )
    moment = timezone.localtime(signalement.date).strftime('%d/%m/%Y à %H h %M')
    contenu = (
        f"L'utilisateur {utilisateur.pseudonyme} a exprimé à Titou une situation grave le {moment} : "
        f"{signalement.get_nature_display().lower()}. "
        + ('Sa personne de confiance a été prévenue par e-mail. ' if personne_prevenue else '')
        + "Les numéros d'urgence et un professionnel lui ont été proposés. Le contenu des messages reste "
        "confidentiel ; suivez le protocole de l'équipe pour les situations à risque."
    )
    for administrateur in Administrateur.objects.filter(is_active=True):
        notifier(administrateur, 'Situation à risque signalée', contenu)
    return signalement
