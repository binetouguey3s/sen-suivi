"""Profil de tendance : résumé compact et anonyme de l'état d'un utilisateur.

C'est la seule chose que le modèle de langage reçoit sur la personne, et
seulement si elle y a consenti (préférence « personnalisation_chatbot »).
Jamais de donnée brute : ni le texte du journal, ni les réponses au test,
ni l'identité, ni l'e-mail, ni les conversations. Seulement quelques
mots-clés, par exemple « humeur en baisse sur 7 jours, journal irrégulier ».
"""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.chatbot.models import MessageChatbot, TypeExpediteur

from .models import AutoEvaluation, NiveauHumeur, SuiviHumeur, TypeEvaluation
from .services import SEUIL_SUGGESTION_PROFESSIONNELS

PREFERENCE_CONSENTEMENT = 'personnalisation_chatbot'

VALEUR_HUMEUR = {
    NiveauHumeur.TRES_MAL: 1,
    NiveauHumeur.MAL: 2,
    NiveauHumeur.NEUTRE: 3,
    NiveauHumeur.BIEN: 4,
    NiveauHumeur.TRES_BIEN: 5,
}
# Écart moyen (en niveaux d'humeur) entre le début et la fin de la période
# à partir duquel on parle de hausse ou de baisse
ECART_TENDANCE = 0.5
ENTREES_MIN_TENDANCE = 3
# Journal considéré comme arrêté au-delà de ce nombre de jours sans entrée
JOURS_ARRET_JOURNAL = 4
# Sur 14 jours, au moins 10 entrées : journal quotidien
FENETRE_REGULARITE, ENTREES_REGULIERES = 14, 10
THEMES_MAX = 2
LIBELLE_TYPE = {TypeEvaluation.STRESS: 'stress', TypeEvaluation.ANXIETE: 'inquiétude', TypeEvaluation.FATIGUE: 'fatigue'}


def a_consenti(compte) -> bool:
    """Consentement explicite : absent ou faux, aucune personnalisation."""
    return (compte.preferences or {}).get(PREFERENCE_CONSENTEMENT) is True


def _tendance(valeurs: list[int]) -> str | None:
    """Hausse, baisse ou stable, en comparant la première et la seconde moitié."""
    if len(valeurs) < ENTREES_MIN_TENDANCE:
        return None
    milieu = len(valeurs) // 2
    debut, fin = valeurs[:milieu], valeurs[milieu:]
    ecart = sum(fin) / len(fin) - sum(debut) / len(debut)
    if ecart >= ECART_TENDANCE:
        return 'en hausse'
    if ecart <= -ECART_TENDANCE:
        return 'en baisse'
    return 'stable'


def _humeur(utilisateur, aujourd_hui) -> list[str]:
    entrees = list(
        SuiviHumeur.objects.filter(utilisateur=utilisateur, date__gt=aujourd_hui - timedelta(days=30))
        .order_by('date')
        .values_list('date', 'score_humeur')
    )
    elements = []
    for jours in (7, 30):
        valeurs = [VALEUR_HUMEUR[s] for d, s in entrees if d > aujourd_hui - timedelta(days=jours)]
        tendance = _tendance(valeurs)
        if tendance:
            elements.append(f'humeur {tendance} sur {jours} jours')
    return elements


def _regularite(utilisateur, aujourd_hui) -> list[str]:
    derniere = SuiviHumeur.objects.filter(utilisateur=utilisateur).order_by('-date').values_list('date', flat=True).first()
    if derniere is None:
        return []
    silence = (aujourd_hui - derniere).days
    if silence >= JOURS_ARRET_JOURNAL:
        return [f'journal arrêté depuis {silence} jours']
    recentes = SuiviHumeur.objects.filter(
        utilisateur=utilisateur, date__gt=aujourd_hui - timedelta(days=FENETRE_REGULARITE)
    ).count()
    return ['journal quotidien' if recentes >= ENTREES_REGULIERES else 'journal irrégulier']


def _dernier_test(utilisateur, aujourd_hui) -> list[str]:
    evaluations = list(AutoEvaluation.objects.filter(utilisateur=utilisateur).order_by('-date'))
    if not evaluations:
        return []
    # Dernier résultat de chaque type : seuls les niveaux modérés ou élevés comptent
    derniers = {}
    for evaluation in evaluations:
        derniers.setdefault(evaluation.type_evaluation, evaluation)
    elements = []
    for type_evaluation, evaluation in sorted(derniers.items(), key=lambda e: -e[1].score_de_tendance):
        if evaluation.score_de_tendance > SEUIL_SUGGESTION_PROFESSIONNELS:
            niveau = 'élevé' if evaluation.score_de_tendance > 66 else 'modéré'
            libelle = LIBELLE_TYPE[type_evaluation]
            de = "d'" if libelle[0] in 'aeiouéèêi' else 'de '
            elements.append(f'niveau {de}{libelle} {niveau} au dernier test')
    jours = (aujourd_hui - timezone.localtime(evaluations[0].date).date()).days
    elements.append('dernier test aujourd\'hui' if jours == 0 else f'dernier test il y a {jours} jours')
    return elements


def _themes(utilisateur, maintenant) -> list[str]:
    """Thématiques des ressources évoquées par Titou dans les échanges conservés."""
    themes = (
        MessageChatbot.objects.filter(
            conversation__utilisateur=utilisateur,
            type_expediteur=TypeExpediteur.BOT,
            ressource__isnull=False,
            date_envoi__gte=maintenant - timedelta(days=30),
        )
        .values('ressource__thematique')
        .annotate(nombre=Count('id'))
        .order_by('-nombre', 'ressource__thematique')[:THEMES_MAX]
    )
    noms = [t['ressource__thematique'].lower() for t in themes]
    return [f"thèmes fréquents : {', '.join(noms)}"] if noms else []


def profil_tendance(utilisateur) -> list[str]:
    """Mots-clés décrivant la tendance récente, sans aucune donnée brute."""
    maintenant = timezone.now()
    aujourd_hui = timezone.localdate()
    return (
        _humeur(utilisateur, aujourd_hui)
        + _regularite(utilisateur, aujourd_hui)
        + _dernier_test(utilisateur, aujourd_hui)
        + _themes(utilisateur, maintenant)
    )
