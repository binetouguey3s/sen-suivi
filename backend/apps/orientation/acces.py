"""Accès à la mise en relation : offre de lancement, puis accès payant.

RÈGLE ÉTHIQUE ABSOLUE — ce qui reste gratuit pour toujours, quelle que soit la
date : le chatbot et le mode vocal, l'orientation d'urgence et les numéros
d'écoute, le journal d'humeur et l'auto-évaluation, la bibliothèque et les
lieux de détente, le forum, et la CONSULTATION de la liste des professionnels
et de leurs profils. Seule la création d'une demande de mise en relation est
concernée par ce module.

Et surtout : une personne en situation de détresse ne voit jamais d'écran de
paiement, de compteur ni de tarif. Sa mise en relation est toujours gratuite
(voir `en_detresse` ci-dessous et le jeton d'urgence dans urgence.py).
"""

from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from .models import AccesMiseEnRelation, StatutAcces


def fin_offre(utilisateur) -> date | None:
    """Dernier jour de gratuité, ou None si l'offre n'a pas de fin."""
    if settings.OFFRE_MODE == 'individuelle':
        inscription = timezone.localtime(utilisateur.date_creation).date()
        return inscription + timedelta(days=settings.OFFRE_DUREE_JOURS - 1)
    if not settings.OFFRE_DATE_FIN:
        return None
    return date.fromisoformat(str(settings.OFFRE_DATE_FIN))


def acces_paye_jusqu_au(utilisateur, aujourd_hui: date) -> date | None:
    acces = (
        AccesMiseEnRelation.objects.filter(utilisateur=utilisateur, statut=StatutAcces.ACTIF, date_fin__gte=aujourd_hui)
        .order_by('-date_fin')
        .first()
    )
    return acces.date_fin if acces else None


def etat_acces(utilisateur, en_detresse: bool = False) -> dict:
    """État de l'accès à la mise en relation, tel que l'interface l'affiche."""
    # RÈGLE ÉTHIQUE : en détresse, ni compteur, ni écran de paiement, ni tarif
    if en_detresse:
        return {'urgence': True, 'offre_active': False, 'jours_restants': None, 'verrouille': False, 'tarif_fcfa': None}

    aujourd_hui = timezone.localdate()
    fin = fin_offre(utilisateur)
    offre_active = fin is None or aujourd_hui <= fin
    paye_jusqu_au = acces_paye_jusqu_au(utilisateur, aujourd_hui)
    verrouille = not offre_active and paye_jusqu_au is None
    return {
        'urgence': False,
        'offre_active': offre_active,
        # Compteur discret en jours, jamais en heures ni en secondes
        'jours_restants': (fin - aujourd_hui).days + 1 if offre_active and fin else None,
        'acces_paye_jusqu_au': paye_jusqu_au,
        'verrouille': verrouille,
        # Aucun tarif tant que l'offre gratuite court : on informe, on ne met pas la pression
        'tarif_fcfa': settings.ACCES_TARIF_FCFA if verrouille else None,
        'duree_acces_jours': settings.ACCES_DUREE_JOURS if verrouille else None,
    }


def peut_demander(utilisateur, en_detresse: bool = False) -> bool:
    """Une demande de mise en relation peut-elle partir sans paiement ?"""
    return not etat_acces(utilisateur, en_detresse)['verrouille']
