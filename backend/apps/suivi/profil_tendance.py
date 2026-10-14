"""Profil de tendance : résumé compact et anonyme de l'état d'un utilisateur.

C'est la seule chose que le modèle de langage reçoit sur la personne, et
seulement si elle y a consenti (préférence « personnalisation_chatbot »).
Jamais de donnée brute : ni le texte du journal, ni les réponses au test,
ni l'identité, ni l'e-mail, ni les conversations. Seulement quelques
mots-clés, par exemple « humeur en baisse sur 7 jours, journal irrégulier »,
complétés par ce que la personne a choisi de dire dans l'onboarding
(« préoccupations : stress, sommeil »). Le prénom, lui, voyage à part.
"""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.chatbot.models import MessageChatbot, TypeExpediteur

from . import libelles_onboarding as libelles
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

# Limites du microservice IA (MessageEntree.profil_tendance) : au-delà, il refuse le message
ELEMENTS_MAX, LONGUEUR_MAX = 10, 80
# Place toujours gardée à l'onboarding, même quand la tendance du journal est longue
ONBOARDING_MIN = 3


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


def _liste(reponses: dict, cle: str) -> list[str]:
    valeur = reponses.get(cle)
    if isinstance(valeur, str):
        valeur = [valeur]
    return [v for v in valeur if isinstance(v, str)] if isinstance(valeur, list) else []


def _element(intitule: str, valeurs: list[str], table: dict[str, str]) -> str | None:
    """« intitulé : libellé, libellé », sans dépasser la longueur permise.

    Les codes inconnus sont ignorés ; les derniers libellés sont retirés plutôt
    que coupés au milieu d'un mot.
    """
    noms = [table[v] for v in valeurs if v in table]
    if not noms:
        return None
    texte = f'{intitule} : {noms[0]}'
    for nom in noms[1:]:
        if len(f'{texte}, {nom}') > LONGUEUR_MAX:
            break
        texte = f'{texte}, {nom}'
    return texte[:LONGUEUR_MAX]


def _onboarding(utilisateur) -> list[str]:
    """Réponses de l'onboarding en mots-clés, de la plus à la moins utile au chatbot.

    Seulement les champs remplis (un onboarding passé peut être partiel).
    Jamais : genre, tranche d'âge, spiritualité détaillée, humeur ou énergie
    de départ (le journal fait foi), « plus à l'aise avec ».
    """
    reponses = (utilisateur.preferences or {}).get('onboarding')
    if not isinstance(reponses, dict):
        return []
    moments, formats = _liste(reponses, 'moments'), _liste(reponses, 'formats')
    echange = reponses.get('echange_pro')
    elements = [
        _element('préoccupations', _liste(reponses, 'preoccupations'), libelles.PREOCCUPATIONS)
        or ('préoccupations : rien de particulier' if reponses.get('rien_de_particulier') is True else None),
        _element('ce qui fait du bien', _liste(reponses, 'bien_etre'), libelles.BIEN_ETRE),
        _element('moments préférés' if len(moments) > 1 else 'moment préféré', moments, libelles.MOMENTS),
        _element('formats préférés' if len(formats) > 1 else 'format préféré', formats, libelles.FORMATS),
        _element('durée', _liste(reponses, 'duree'), libelles.DUREES),
        _element('situation', _liste(reponses, 'situation'), libelles.SITUATIONS),
        _element('langue', _liste(reponses, 'langue'), libelles.LANGUES),
        _element('souhaite échanger avec un professionnel', _liste(reponses, 'echange_pro'), libelles.ECHANGES_PRO),
        None if echange == 'pas_maintenant'
        else _element("métiers qui l'intéressent", _liste(reponses, 'metiers'), libelles.METIERS),
    ]
    return [e for e in elements if e]


def metiers_preferes(utilisateur) -> list[str]:
    """Spécialités (codes SpecialitePro) choisies dans l'onboarding, pour l'orientation."""
    reponses = (utilisateur.preferences or {}).get('onboarding')
    if not isinstance(reponses, dict) or reponses.get('echange_pro') == 'pas_maintenant':
        return []
    return [m for m in _liste(reponses, 'metiers') if m in libelles.METIERS]


def profil_tendance(utilisateur) -> list[str]:
    """Mots-clés décrivant la tendance récente et les préférences, sans aucune donnée brute."""
    maintenant = timezone.now()
    aujourd_hui = timezone.localdate()
    tendance = (
        _humeur(utilisateur, aujourd_hui)
        + _regularite(utilisateur, aujourd_hui)
        + _dernier_test(utilisateur, aujourd_hui)
        + _themes(utilisateur, maintenant)
    )
    onboarding = _onboarding(utilisateur)
    # Le journal fait foi et passe d'abord, sans jamais prendre toute la place
    tendance = tendance[: ELEMENTS_MAX - min(len(onboarding), ONBOARDING_MIN)]
    return [e[:LONGUEUR_MAX] for e in tendance + onboarding[: ELEMENTS_MAX - len(tendance)]]
