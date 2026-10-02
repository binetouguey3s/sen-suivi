"""Modération automatique du forum.

Principe directeur : le forum doit rester un endroit où l'on PEUT dire qu'on va
mal. On bloque l'AGRESSION, jamais la SOUFFRANCE.

Trois niveaux, dans cet ordre :
- niveau 0, règles sans modèle (rapide et gratuit) : détresse, insultes
  évidentes, coordonnées personnelles, spam ;
- niveau 1, classification par le modèle de modération (MODERATION_MODELE du
  .env), qui répond en JSON strict ;
- niveau 2, décision : publier, publier en accompagnant la personne, bloquer
  avec un message pédagogique, bloquer silencieusement, ou faire attendre une
  validation humaine. En cas de doute, on ne publie pas et on ne bloque pas
  définitivement : on fait attendre.

Jamais le texte d'un message dans les journaux : seulement la décision.
"""

import hashlib
import json
import logging
import os
import re
import unicodedata
from collections import OrderedDict
from dataclasses import asdict, dataclass

import httpx

from app.config.lexique_moderation import (
    INSULTES_CIBLEES,
    INSULTES_FORTES,
    MARQUEURS_CIBLAGE,
    MARQUEURS_RECIT,
    NUMEROS_AUTORISES,
    RESEAUX_SOCIAUX,
    SPAM,
)
from app.detecteur_detresse import detecter_detresse

journal = logging.getLogger(__name__)

CATEGORIES = {
    'CONFORME', 'INSULTE', 'HARCELEMENT', 'HAINE', 'CONTENU_SEXUEL', 'AGRESSION_SEXUELLE',
    'DONNEES_PERSONNELLES', 'SPAM', 'DETRESSE',
}


class Decision:
    PUBLIER = 'PUBLIER'
    # Publié, ET message privé à l'auteur avec les numéros d'écoute, ET signalement admin
    PUBLIER_ACCOMPAGNER = 'PUBLIER_ACCOMPAGNER'
    BLOQUER = 'BLOQUER'
    # Blocage immédiat et file administrateur en priorité haute
    BLOQUER_PRIORITAIRE = 'BLOQUER_PRIORITAIRE'
    BLOQUER_SILENCIEUX = 'BLOQUER_SILENCIEUX'
    ATTENTE_HUMAINE = 'ATTENTE_HUMAINE'


@dataclass
class ResultatModeration:
    categorie: str
    gravite: int
    extrait: str
    raison: str
    decision: str = ''
    message: str = ''
    niveau: str = 'REGLES'  # REGLES, MODELE ou REPLI (modèle indisponible)
    priorite: int = 0  # 0 aucune, 1 normale, 2 haute

    def en_dict(self) -> dict:
        return asdict(self)


# --- Normalisation : déjouer les contournements ---------------------------------

_CHIFFRES_EN_LETTRES = str.maketrans({'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'})


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni chiffres-lettres, lettres isolées recollées,
    lettres répétées réduites à une seule, ponctuation remplacée par des espaces."""
    texte = unicodedata.normalize('NFKD', texte or '').encode('ascii', 'ignore').decode('ascii').lower()
    # Chiffres utilisés comme lettres, seulement à l'intérieur d'un mot (« c0nnard ») :
    # les nombres eux-mêmes (numéros, horaires) restent intacts
    texte = re.sub(r'(?<=[a-z])[0-9@$]+|[0-9@$]+(?=[a-z])', lambda m: m.group().translate(_CHIFFRES_EN_LETTRES), texte)
    # « s.a.l.o.p.e », « s a l o p e », « s-a-l-o-p-e » : lettres isolées recollées
    texte = re.sub(r'\b(?:[a-z][\s._*\-]){2,}[a-z]\b', lambda m: re.sub(r'[\s._*\-]', '', m.group()), texte)
    texte = re.sub(r'([a-z])\1+', r'\1', texte)
    texte = re.sub(r"[^a-z0-9]+", ' ', texte)
    return f' {texte.strip()} '


def _motif(terme: str) -> re.Pattern:
    """Le terme comme mot entier, pluriel et féminin admis (« conards », « idiote »)."""
    return re.compile(r'(?<![a-z])' + re.escape(normaliser(terme).strip()) + r'(?:e?s)?(?![a-z])')


_FORTES = [(t, _motif(t)) for t in INSULTES_FORTES]
_CIBLEES = [(t, _motif(t)) for t in INSULTES_CIBLEES]
_CIBLAGE = [normaliser(m).strip() for m in MARQUEURS_CIBLAGE]
_RECIT = [normaliser(m).strip() for m in MARQUEURS_RECIT]
_RESEAUX = [(r, _motif(r)) for r in RESEAUX_SOCIAUX]
_SPAM = [_motif(s) for s in SPAM]

_LIEN = re.compile(r'(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|sn|net|org|fr|io|me|ly|info|biz)\b\S*', re.IGNORECASE)
_EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
_COMPTE = re.compile(r'(?<![\w.])@[A-Za-z0-9_.]{3,}')
_NUMERO = re.compile(r'(?:\+|00)?\d[\d\s.\-]{6,}\d')


# Petits mots tolérés entre la cible et le mot blessant : « t'es VRAIMENT nul »
_LIAISONS = {'un', 'une', 'des', 'vraiment', 'trop', 'tellement', 'completement', 'grave', 'si', 'qu', 'que', 'le', 'la'}


def _vise_quelqu_un(normalise: str, position: int) -> bool:
    """Le mot blessant est-il adressé à quelqu'un ? Le marqueur (« t'es »,
    « espèce de », « yow »…) doit le précéder directement, à un mot de liaison près."""
    mots = normalise[:position].split()
    if mots and mots[-1] in _LIAISONS:
        mots = mots[:-1]
    fin = ' '.join(mots[-3:])
    return any(fin == m or fin.endswith(' ' + m) for m in _CIBLAGE)


def _extrait(texte: str, terme: str) -> str:
    """Passage du message original à citer dans le message pédagogique."""
    mots = terme.split()
    motif = r'\W*'.join(re.escape(m[:3]) + r'\w*' for m in mots)
    trouve = re.search(motif, unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii'), re.I)
    return texte[trouve.start():trouve.end()] if trouve else terme


# --- Niveau 0 : règles ------------------------------------------------------------

def niveau_0(texte: str) -> ResultatModeration | None:
    """Cas évidents, sans modèle. None : rien d'évident, le modèle décidera."""
    for motif in (_EMAIL,):
        if trouve := motif.search(texte):
            return ResultatModeration('DONNEES_PERSONNELLES', 1, trouve.group(), 'adresse e-mail')
    for trouve in _NUMERO.finditer(texte):
        chiffres = re.sub(r'\D', '', trouve.group())
        if len(chiffres) >= 7 and chiffres not in NUMEROS_AUTORISES:
            return ResultatModeration('DONNEES_PERSONNELLES', 1, trouve.group().strip(), 'numéro de téléphone')
    if trouve := _COMPTE.search(texte):
        return ResultatModeration('DONNEES_PERSONNELLES', 1, trouve.group(), 'compte de réseau social')

    normalise = normaliser(texte)
    if _LIEN.search(texte) or any(m.search(normalise) for m in _SPAM):
        extrait = (_LIEN.search(texte) or re.search(r'.{0,30}', texte)).group()
        return ResultatModeration('SPAM', 1, extrait, 'lien externe ou sollicitation commerciale')
    for reseau, motif in _RESEAUX:
        if motif.search(normalise) and re.search(r'(ajout|contact|ecri|suiv|mon|ma page|dm|pv)', normalise):
            return ResultatModeration('DONNEES_PERSONNELLES', 1, _extrait(texte, reseau), 'compte de réseau social')

    recit = any(m in normalise for m in _RECIT)
    for terme, motif in _FORTES:
        if trouve := motif.search(normalise):
            if recit:
                return None  # une insulte rapportée : témoignage possible, le modèle tranche
            return ResultatModeration('INSULTE', 2, _extrait(texte, terme), 'insulte')
    for terme, motif in _CIBLEES:
        for trouve in motif.finditer(normalise):
            if _vise_quelqu_un(normalise, trouve.start()) and not recit:
                return ResultatModeration('INSULTE', 1, _extrait(texte, terme), 'mot blessant adressé à quelqu’un')
    return None


# --- Niveau 1 : modèle de modération ------------------------------------------------

POLITIQUE = """Tu es le modérateur du forum de Sen Suivi, une plateforme sénégalaise de bien-être \
mental. Le forum est anonyme et doit rester un endroit où l'on PEUT dire qu'on va mal.

Principe absolu : on sanctionne l'AGRESSION, jamais la SOUFFRANCE.
Un récit de violence SUBIE, un témoignage de souffrance, un partage d'expérience difficile ne \
sont PAS des infractions : ils sont CONFORMES, éventuellement marqués DETRESSE. Seuls les \
propos DIRIGÉS CONTRE quelqu'un sont sanctionnés. Les messages peuvent mêler français et wolof.

Catégories :
- CONFORME : message acceptable, y compris un témoignage difficile
- INSULTE : grossièretés, mépris, moquerie visant une personne
- HARCELEMENT : attaque répétée ou ciblée contre un membre
- HAINE : propos visant un groupe (origine, ethnie, religion, genre, orientation, handicap)
- CONTENU_SEXUEL : contenu explicite ou drague insistante
- AGRESSION_SEXUELLE : sollicitation, menace ou propos sexuel visant quelqu'un
- DONNEES_PERSONNELLES : coordonnées, ou identification d'un tiers (nom complet, adresse, école)
- SPAM : publicité, sollicitation commerciale
- DETRESSE : la personne exprime une souffrance intense qui la concerne elle-même

Gravité : 1 légère, 2 nette, 3 grave.

Exemples :
1. « Mon oncle m'a frappée pendant des années, je n'arrive pas à en parler à ma famille. »
   -> {"categorie": "CONFORME", "gravite": 1, "extrait_problematique": "", "raison": "récit de violence subie"}
2. « Toi qui défends ton oncle, je vais venir te frapper aussi. »
   -> {"categorie": "HARCELEMENT", "gravite": 3, "extrait_problematique": "je vais venir te frapper", "raison": "menace contre un membre"}
3. « Au lycée, ils me traitaient de grosse vache tous les jours, j'en pleure encore. »
   -> {"categorie": "CONFORME", "gravite": 1, "extrait_problematique": "", "raison": "témoignage de moqueries subies"}
4. « Avec ton poids, pas étonnant qu'on te traite de grosse vache. »
   -> {"categorie": "INSULTE", "gravite": 2, "extrait_problematique": "pas étonnant qu'on te traite de grosse vache", "raison": "moquerie visant un membre"}
5. « Je n'en peux plus, je ne vois plus aucune raison de continuer à vivre. »
   -> {"categorie": "DETRESSE", "gravite": 3, "extrait_problematique": "", "raison": "souffrance intense exprimée par l'auteur"}
6. « Les gens de cette ethnie sont tous des voleurs, il faut les chasser du quartier. »
   -> {"categorie": "HAINE", "gravite": 3, "extrait_problematique": "tous des voleurs, il faut les chasser", "raison": "propos haineux visant un groupe"}

Réponds UNIQUEMENT par un objet JSON, sans aucun texte autour :
{"categorie": "...", "gravite": 1, "extrait_problematique": "...", "raison": "..."}
L'extrait est copié mot pour mot du message, vide si le message est CONFORME ou DETRESSE."""


def _reglages() -> dict:
    return {
        'url': (os.environ.get('MODERATION_URL_BASE') or os.environ.get('LLM_URL_BASE', '')).rstrip('/'),
        'cle': os.environ.get('MODERATION_CLE_API') or os.environ.get('LLM_CLE_API', ''),
        'modele': os.environ.get('MODERATION_MODELE', ''),
        'effort': os.environ.get('MODERATION_EFFORT_RAISONNEMENT', ''),
        'delai': float(os.environ.get('MODERATION_DELAI_SECONDES', '8')),
        'longueur_min': int(os.environ.get('MODERATION_LONGUEUR_MIN', '20')),
        'cache': int(os.environ.get('MODERATION_CACHE_TAILLE', '2000')),
    }


class ModeleIndisponible(Exception):
    pass


def niveau_1(texte: str) -> ResultatModeration:
    """Classification par le modèle ; lève ModeleIndisponible au moindre souci."""
    r = _reglages()
    if not (r['url'] and r['cle'] and r['modele']):
        raise ModeleIndisponible('modèle de modération non configuré')
    corps = {
        'model': r['modele'],
        'messages': [{'role': 'system', 'content': POLITIQUE}, {'role': 'user', 'content': texte}],
        'temperature': 0,
        'max_tokens': 400,
    }
    if r['effort']:
        corps['reasoning_effort'] = r['effort']
    try:
        reponse = httpx.post(
            f"{r['url']}/chat/completions", headers={'Authorization': f"Bearer {r['cle']}"}, json=corps, timeout=r['delai']
        )
        reponse.raise_for_status()
        contenu = reponse.json()['choices'][0]['message']['content'] or ''
        brut = json.loads(re.search(r'\{.*\}', contenu, re.DOTALL).group())
        categorie = str(brut['categorie']).upper()
        gravite = int(brut.get('gravite', 1))
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError, AttributeError) as erreur:
        raise ModeleIndisponible(type(erreur).__name__) from erreur
    if categorie not in CATEGORIES or gravite not in (1, 2, 3):
        raise ModeleIndisponible('réponse hors format')
    extrait = str(brut.get('extrait_problematique') or '')
    # Un extrait qui n'est pas dans le message serait une invention : on ne le cite pas
    if extrait and extrait.lower() not in texte.lower():
        extrait = ''
    return ResultatModeration(categorie, gravite, extrait, str(brut.get('raison') or ''), niveau='MODELE')


# --- Niveau 2 : décision -------------------------------------------------------------

MESSAGE_ACCOMPAGNEMENT = (
    "Votre message a bien été publié. Ce que vous traversez semble lourd : vous n'êtes pas obligé·e "
    "de le porter seul·e. Le 800 805 805 (numéro vert d'écoute) répond gratuitement à toute heure, "
    "et le 1515 (SAMU) en cas d'urgence. Titou, l'assistant de Sen Suivi, est aussi là pour vous écouter."
)
MESSAGE_ATTENTE = (
    "Votre message est en cours de relecture par l'équipe de Sen Suivi. Il sera publié très vite "
    "s'il respecte la charte du forum."
)
# Ce qui pose problème, dit simplement. Les propos blessants ne sont jamais
# répétés à l'auteur : l'extrait reste visible pour l'équipe, dans la file admin.
MOTIF_LISIBLE = {
    'INSULTE': 'contient des mots blessants ou grossiers',
    'HARCELEMENT': 'contient des propos qui visent un membre de façon insistante ou menaçante',
    'HAINE': 'contient des propos qui visent un groupe de personnes',
    'CONTENU_SEXUEL': 'contient un contenu à caractère sexuel',
    'AGRESSION_SEXUELLE': 'contient des propos sexuels visant quelqu’un',
    'DONNEES_PERSONNELLES': 'contient des coordonnées ou des informations qui permettent d’identifier quelqu’un',
}


def _message_blocage(resultat: ResultatModeration) -> str:
    """Toujours respectueux : ce qui pose problème, et une invitation à reformuler.

    Seules les coordonnées sont citées (« 77 123 45 67 »), pour qu'on sache quoi
    retirer ; une insulte ou un propos blessant n'est jamais répété à l'auteur.
    """
    motif = MOTIF_LISIBLE.get(resultat.categorie, 'ne respecte pas la charte du forum')
    if resultat.categorie == 'DONNEES_PERSONNELLES':
        cite = f' (« {resultat.extrait} »)' if resultat.extrait else ''
        conseil = " Le forum est anonyme : pour votre sécurité, n'y partagez ni numéro, ni e-mail, ni compte."
    else:
        cite = ''
        conseil = ' Vous pouvez tout à fait exprimer ce que vous ressentez, avec d’autres mots et sans viser personne.'
    return (
        f"Votre message n'a pas été publié : il {motif}{cite}.{conseil} "
        "Merci de le reformuler, ou de demander un réexamen par l'équipe si vous pensez qu'il s'agit d'une erreur."
    )


def decider(resultat: ResultatModeration) -> ResultatModeration:
    c, g = resultat.categorie, resultat.gravite
    if c == 'CONFORME':
        resultat.decision = Decision.PUBLIER
    elif c == 'DETRESSE':
        # Jamais de blocage : bloquer quelqu'un qui souffre, c'est le faire taire
        resultat.decision, resultat.message, resultat.priorite = Decision.PUBLIER_ACCOMPAGNER, MESSAGE_ACCOMPAGNEMENT, 2
    elif c == 'SPAM':
        resultat.decision = Decision.BLOQUER_SILENCIEUX
    elif c in ('HARCELEMENT', 'HAINE', 'AGRESSION_SEXUELLE'):
        resultat.decision, resultat.message, resultat.priorite = Decision.BLOQUER_PRIORITAIRE, _message_blocage(resultat), 2
    elif g >= 3:
        # Insulte, contenu sexuel ou données personnelles de gravité 3 : un humain confirme
        resultat.decision, resultat.message, resultat.priorite = Decision.BLOQUER_PRIORITAIRE, _message_blocage(resultat), 2
    else:
        resultat.decision, resultat.message = Decision.BLOQUER, _message_blocage(resultat)
    return resultat


def _attente(raison: str, niveau: str = 'REPLI') -> ResultatModeration:
    return ResultatModeration(
        'CONFORME', 0, '', raison, decision=Decision.ATTENTE_HUMAINE, message=MESSAGE_ATTENTE, niveau=niveau, priorite=1
    )


# --- Orchestration, cache et journal -------------------------------------------------

_cache: OrderedDict[str, dict] = OrderedDict()


def _condensat(texte: str) -> str:
    return hashlib.sha256(normaliser(texte).encode()).hexdigest()


def moderer(texte: str) -> ResultatModeration:
    texte = (texte or '').strip()
    condensat = _condensat(texte)
    resultat = _moderer(texte, condensat)
    # Journal anonymisé : la décision, jamais le texte (seulement le début du condensat)
    journal.info('Modération %s : %s (%s, gravité %s)', condensat[:10], resultat.decision, resultat.categorie, resultat.gravite)
    return resultat


def _moderer(texte: str, condensat: str) -> ResultatModeration:
    r = _reglages()
    # La détresse passe avant tout : jamais bloquée, toujours accompagnée
    detresse = detecter_detresse(texte)
    regle = niveau_0(texte)
    if detresse:
        if regle and regle.categorie == 'INSULTE':
            # Souffrance ET agression dans le même message : un humain tranche
            resultat = _attente('détresse et propos blessants mêlés', 'REGLES')
            resultat.priorite, resultat.message = 2, MESSAGE_ACCOMPAGNEMENT
            return resultat
        return decider(ResultatModeration('DETRESSE', 3, '', 'mots de détresse'))
    if regle:
        return decider(regle)
    # Message court sans rien d'évident : pas besoin du modèle
    if len(texte) < r['longueur_min']:
        return decider(ResultatModeration('CONFORME', 1, '', 'message court sans problème', niveau='REGLES'))
    if condensat in _cache:
        _cache.move_to_end(condensat)
        return ResultatModeration(**_cache[condensat])
    try:
        resultat = decider(niveau_1(texte))
    except ModeleIndisponible as erreur:
        # On ne publie jamais sans contrôle : tout part en file humaine
        journal.warning('Modèle de modération indisponible : %s', erreur)
        return _attente('modèle indisponible')
    _cache[condensat] = resultat.en_dict()
    while len(_cache) > r['cache']:
        _cache.popitem(last=False)
    return resultat
