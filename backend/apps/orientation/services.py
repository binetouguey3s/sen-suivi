"""Suggestion du professionnel le plus adapté : un algorithme déterministe.

Jamais le modèle de langage : la recommandation doit pouvoir s'expliquer et se
reproduire. Les critères sont comparés dans cet ordre, le suivant ne servant
qu'à départager les ex æquo du précédent :
1. adéquation entre les besoins de la personne et le métier ou les domaines
   déclarés par le professionnel ;
2. langue commune ;
3. proximité géographique ;
4. disponibilité (accepte de nouvelles demandes) ;
5. équité : le moins sollicité ces 30 derniers jours passe devant, pour ne pas
   envoyer toutes les demandes au même professionnel.

La suggestion n'enferme jamais le choix : la liste complète reste consultable.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.chatbot.models import MessageChatbot, TypeExpediteur
from apps.comptes.models import Professionnel, StatutValidationPro
from apps.suivi.models import AutoEvaluation
from apps.suivi.services import SEUIL_SUGGESTION_PROFESSIONNELS

from .correspondances import BESOIN_PAR_TEST, BESOIN_PAR_THEMATIQUE, BESOINS, MARQUEURS_WOLOF

BESOINS_MAX = 3
FENETRE_EQUITE_JOURS = 30
MARQUEURS_WOLOF_MIN = 2


def normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize('NFKD', texte or '').encode('ascii', 'ignore').decode('ascii')
    return sans_accents.lower().replace('’', "'")


def besoins_du_texte(texte: str) -> list[str]:
    """Besoins évoqués dans un texte libre, dans l'ordre de la table."""
    normalise = normaliser(texte)
    return [code for code, besoin in BESOINS.items() if any(mot in normalise for mot in besoin['mots'])]


def parle_wolof(textes: list[str]) -> bool:
    mots = set(re.findall(r'[a-z]+', normaliser(' '.join(textes))))
    return len(mots & MARQUEURS_WOLOF) >= MARQUEURS_WOLOF_MIN


def besoins_de(utilisateur, textes: list[str] | None = None) -> list[str]:
    """Besoins de la personne, du plus au moins prioritaire.

    D'abord ce qu'elle dit elle-même (messages récents, le plus récent en
    premier), puis ses derniers tests modérés ou élevés, puis les thématiques
    des ressources que Titou lui a proposées.
    """
    ordre: list[str] = []

    def ajouter(code):
        if code and code not in ordre:
            ordre.append(code)

    for texte in reversed(textes or []):
        for code in besoins_du_texte(texte):
            ajouter(code)

    if utilisateur is not None:
        derniers = {}
        for evaluation in AutoEvaluation.objects.filter(utilisateur=utilisateur).order_by('-date'):
            derniers.setdefault(evaluation.type_evaluation, evaluation.score_de_tendance)
        for type_evaluation, score in sorted(derniers.items(), key=lambda e: -e[1]):
            if score > SEUIL_SUGGESTION_PROFESSIONNELS:
                ajouter(BESOIN_PAR_TEST.get(type_evaluation))

        themes = (
            MessageChatbot.objects.filter(
                conversation__utilisateur=utilisateur,
                type_expediteur=TypeExpediteur.BOT,
                ressource__isnull=False,
                date_envoi__gte=timezone.now() - timedelta(days=30),
            )
            .values('ressource__thematique')
            .annotate(nombre=Count('id'))
            .order_by('-nombre', 'ressource__thematique')
        )
        for theme in themes:
            ajouter(BESOIN_PAR_THEMATIQUE.get(theme['ressource__thematique'].lower()))

    return ordre[:BESOINS_MAX]


def langues_de(professionnel) -> set[str]:
    return {normaliser(l).strip() for l in re.split(r'[,/;]| et ', professionnel.langue or '') if l.strip()}


def _adequation(professionnel, besoins: list[str]) -> tuple[int, list[str]]:
    """Points d'adéquation et besoins réellement couverts par ce professionnel.

    Le premier besoin pèse le plus. Métier indiqué pour ce besoin : de 3 points
    (métier le plus indiqué) à 1 ; domaine déclaré qui en parle : +2.
    """
    domaines = normaliser(' '.join(professionnel.domaines or []))
    total, couverts = 0, []
    for rang, code in enumerate(besoins):
        besoin = BESOINS[code]
        poids = len(besoins) - rang
        points = 0
        if professionnel.specialite in besoin['metiers']:
            points += 3 - min(besoin['metiers'].index(professionnel.specialite), 2)
        if any(mot in domaines for mot in besoin['mots']):
            points += 2
        if points:
            couverts.append(code)
            total += points * poids
    return total, couverts


@dataclass
class Suggestion:
    professionnel: Professionnel
    raison: str
    besoins: list[str] = field(default_factory=list)
    criteres: dict = field(default_factory=dict)


def _raison(professionnel, couverts: list[str], ville_commune: bool, langue: str | None) -> str:
    """Phrase courte et factuelle : pourquoi ce professionnel-là."""
    morceaux = []
    if couverts:
        libelles = [BESOINS[c]['libelle'] for c in couverts[:2]]
        morceaux.append('accompagne ' + ', ainsi que '.join(libelles))
    lieu = f'consulte à {professionnel.ville}' if ville_commune or not professionnel.consultation_distance else None
    if lieu:
        morceaux.append(lieu)
    if professionnel.consultation_distance:
        morceaux.append('propose des échanges à distance')
    if langue:
        morceaux.append(f'parle {langue}')
    if not morceaux:
        morceaux.append('est disponible pour de nouvelles demandes')
    phrase = ', '.join(morceaux[:-1]) + (' et ' if len(morceaux) > 1 else '') + morceaux[-1]
    return f'{professionnel.get_specialite_display()}, {professionnel.nom} {phrase}.'


def classer(besoins: list[str], langue: str | None = None, ville: str | None = None) -> list[Suggestion]:
    """Tous les professionnels validés, du plus au moins adapté."""
    depuis = timezone.now() - timedelta(days=FENETRE_EQUITE_JOURS)
    professionnels = Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE).annotate(
        sollicitations=Count('demandes_contact_recues', filter=Q(demandes_contact_recues__date__gte=depuis))
    )
    langue_n = normaliser(langue).strip() if langue else None
    ville_n = normaliser(ville).strip() if ville else None

    classes = []
    for pro in professionnels:
        points, couverts = _adequation(pro, besoins)
        langue_commune = bool(langue_n) and langue_n in langues_de(pro)
        ville_commune = bool(ville_n) and (ville_n in normaliser(pro.ville) or normaliser(pro.ville).split()[0] in ville_n)
        criteres = {
            'adequation': points,
            'langue_commune': langue_commune,
            'proximite': ville_commune,
            'disponible': pro.accepte_demandes,
            'sollicitations': pro.sollicitations,
        }
        # Tri lexicographique dans l'ordre des critères ; l'identifiant garantit
        # un résultat reproductible entre deux professionnels en tout point égaux
        cle = (-points, not langue_commune, not ville_commune, not pro.accepte_demandes, pro.sollicitations, pro.pk)
        raison = _raison(pro, couverts, ville_commune, langue if langue_commune else None)
        classes.append((cle, Suggestion(pro, raison, couverts, criteres)))
    return [s for _, s in sorted(classes, key=lambda c: c[0])]


def suggerer(utilisateur=None, textes: list[str] | None = None, besoins: list[str] | None = None,
             langue: str | None = None, ville: str | None = None) -> Suggestion | None:
    """LE professionnel mis en avant : le mieux classé parmi ceux qui acceptent
    de nouvelles demandes. Aucun si personne n'est disponible."""
    if besoins is None:
        besoins = besoins_de(utilisateur, textes)
    if langue is None and textes and parle_wolof(textes):
        langue = 'wolof'
    if ville is None and utilisateur is not None:
        ville = getattr(utilisateur, 'ville', '') or None
    return next((s for s in classer(besoins, langue, ville) if s.professionnel.accepte_demandes), None)
