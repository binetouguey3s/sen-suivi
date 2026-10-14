"""Rappels doux envoyés par n8n : ce que la personne a choisi dans l'onboarding.

- `rappels` et `frequence_rappels` : désactiver le rappel de journal, ou en
  limiter le rythme (« quotidien » : 1 par jour au plus ; « 3_semaine » :
  3 par semaine au plus). Sans réponse, la règle générale s'applique
  (un rappel par RAPPEL_FREQUENCE_MAX_JOURS, tous types confondus).
- `moments` : le moment de la journée où le rappel arrive. Aucun moment
  choisi (ou pas d'onboarding) : le matin.
- Avec le consentement à la personnalisation seulement : une ressource dont
  la thématique répond à une préoccupation, dans le format préféré si possible.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.ressources.models import Ressource, TypeRessource
from apps.suivi.profil_tendance import a_consenti

MOMENTS = ('matin', 'midi', 'soir', 'coucher')
MOMENT_PAR_DEFAUT = 'matin'
# « … pour vous ce soir ? »
MOMENT_DANS_LA_PHRASE = {
    'matin': 'ce matin',
    'midi': 'ce midi',
    'soir': 'ce soir',
    'coucher': 'avant de dormir',
    None: "aujourd'hui",
}

# 3 rappels au plus sur 7 jours glissants
RAPPELS_PAR_SEMAINE, JOURS_SEMAINE = 3, 7

# Préoccupation de l'onboarding → thématiques de la bibliothèque, de la plus à la moins proche
THEMATIQUES_PAR_PREOCCUPATION = {
    'stress': ['stress', 'respiration'],
    'etudes': ['études', 'organisation'],
    'travail': ['travail', 'organisation'],
    'sommeil': ['sommeil'],
    'emotions': ['émotions', 'expression'],
    'confiance': ['confiance en soi'],
    'motivation': ['motivation'],
    'famille': ['famille'],
    'relations': ['relations', 'lien social'],
    'solitude': ['lien social', 'expression'],
    'deuil': ['deuil'],
    'organisation': ['organisation', 'travail'],
    'ecrans': ['numérique'],
    'avenir': ['motivation', 'bien-être'],
}
# Format préféré → type de ressource (aucune vidéo dans la bibliothèque pour l'instant)
TYPE_PAR_FORMAT = {'texte': TypeRessource.ARTICLE, 'audio': TypeRessource.PODCAST, 'exercice': TypeRessource.EXERCICE}


def onboarding(utilisateur) -> dict:
    reponses = (utilisateur.preferences or {}).get('onboarding')
    return reponses if isinstance(reponses, dict) else {}


def _liste(reponses: dict, cle: str) -> list[str]:
    valeur = reponses.get(cle)
    return [v for v in valeur if isinstance(v, str)] if isinstance(valeur, list) else []


def journal_refuse(utilisateur) -> bool:
    """Rappels coupés dans l'onboarding : « Recevoir des rappels » désactivé, ou « Jamais »."""
    reponses = onboarding(utilisateur)
    return reponses.get('rappels') is False or reponses.get('frequence_rappels') == 'jamais'


def moments(utilisateur) -> list[str]:
    choisis = [m for m in _liste(onboarding(utilisateur), 'moments') if m in MOMENTS]
    return choisis or [MOMENT_PAR_DEFAUT]


def frequence_respectee(utilisateur, envois: list) -> bool:
    """`envois` : dates des rappels déjà reçus par la personne (tous types).

    « quotidien » : rien aujourd'hui ; « 3_semaine » : moins de 3 sur 7 jours ;
    sinon, la règle générale : rien pendant RAPPEL_FREQUENCE_MAX_JOURS.
    """
    maintenant = timezone.now()
    frequence = onboarding(utilisateur).get('frequence_rappels')
    if frequence == 'quotidien':
        aujourd_hui = timezone.localdate()
        return not any(timezone.localtime(d).date() == aujourd_hui for d in envois)
    if frequence == '3_semaine':
        return sum(d > maintenant - timedelta(days=JOURS_SEMAINE) for d in envois) < RAPPELS_PAR_SEMAINE
    return not any(d > maintenant - timedelta(days=settings.RAPPEL_FREQUENCE_MAX_JOURS) for d in envois)


def ressource_suggeree(utilisateur) -> Ressource | None:
    """Une ressource qui répond à une préoccupation, avec le consentement seulement.

    Les préoccupations sont parcourues dans l'ordre où la personne les a
    choisies ; à thématique égale, le format préféré passe devant. Parmi les
    meilleures, le choix tourne avec le jour, pour ne pas proposer toujours la même.
    """
    if not a_consenti(utilisateur):
        return None
    reponses = onboarding(utilisateur)
    types_preferes = {TYPE_PAR_FORMAT[f] for f in _liste(reponses, 'formats') if f in TYPE_PAR_FORMAT}
    ressources = list(Ressource.objects.order_by('pk'))
    for preoccupation in _liste(reponses, 'preoccupations'):
        thematiques = THEMATIQUES_PAR_PREOCCUPATION.get(preoccupation, [])
        candidates = [r for r in ressources if r.thematique.strip().lower() in thematiques]
        if not candidates:
            continue
        meilleures = [r for r in candidates if r.type_ressource in types_preferes] or candidates
        return meilleures[timezone.localdate().toordinal() % len(meilleures)]
    return None
