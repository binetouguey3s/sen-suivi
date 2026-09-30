"""Microservice IA (FastAPI), séparé du back-end Django.

Toujours dans cet ordre :
- Nettoyage de l'entrée
- Niveau 0  : détection de détresse (sécurité) — si déclenchée, on s'arrête là,
              le modèle de langage n'est jamais appelé.
- Niveau 1  : classification d'intention. Sans modèle de langage, la réponse
              validée prédéfinie de l'intention est renvoyée ; avec un modèle,
              elle devient le filet de sécurité, car un texte fixe ignore le
              fil de la conversation.
- Niveau 2a : RAG — recherche des ressources validées les plus proches.
- Niveau 2b : génération encadrée par le modèle de langage, à partir de ces
              seules ressources ; sans ressource, ou si la réponse est
              rejetée, mode écoute (accueil, jamais de conseil).
- Validation de la sortie, puis repli en cascade : réponse générée valide,
  sinon réponse prédéfinie de l'intention, sinon ressource la plus proche,
  sinon réponse de repli.

Les derniers échanges de la conversation accompagnent le message, pour que le
modèle suive le fil. Le niveau 0 ne regarde que le message actuel : un
historique ne peut jamais retarder une réponse d'urgence.
"""

import logging
import re
from typing import Annotated, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.classificateur_intention import REPONSE_PAR_INTENTION, classifier
from app.detecteur_detresse import REPONSE_URGENCE, detecter_detresse
from app.generateur_reponse import echeance_totale, ecouter, generation_disponible, generer
from app.moteur_rag import NOMBRE_MAX_RESULTATS, catalogue, indexer_ressources, rechercher, rechercher_plusieurs
from app.validateur_reponse import mots_significatifs, valider

journal = logging.getLogger(__name__)

# Réponse fixe, utilisée quand aucun modèle ne répond et qu'aucune ressource
# ne correspond : elle continue la conversation au lieu de la fermer
REPONSE_REPLI = (
    "Je vous écoute. Pouvez-vous m'en dire un peu plus sur ce que vous vivez en ce moment ? "
    "Vous pouvez aussi explorer la bibliothèque de Sen Suivi ou demander une mise en relation "
    "avec un professionnel."
)
# Variante, pour ne jamais envoyer deux fois de suite le même message de repli
REPONSE_REPLI_BIS = (
    "Je suis toujours là, prenez le temps qu'il vous faut. Si vous préférez parler à quelqu'un, "
    "l'annuaire de Sen Suivi vous permet de demander une mise en relation avec un professionnel."
)

app = FastAPI(title='Sen Suivi — Microservice IA')

# Le front-end (Angular, localhost:4200) et Django n'appellent jamais ce
# service directement depuis le navigateur ; CORS n'ouvre que le strict
# nécessaire pour le développement local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:4200', 'http://localhost:8000'],
    allow_methods=['*'],
    allow_headers=['*'],
)


class EchangePrecedent(BaseModel):
    auteur: Literal['UTILISATEUR', 'BOT']
    contenu: str = Field(max_length=2000)


class MessageEntree(BaseModel):
    message: str
    # Derniers échanges de la conversation, du plus ancien au plus récent
    historique: list[EchangePrecedent] = Field(default_factory=list, max_length=20)
    # Profil de tendance (mots-clés anonymes), seulement si l'utilisateur y a consenti
    profil_tendance: list[Annotated[str, Field(max_length=80)]] = Field(default_factory=list, max_length=10)
    # Compte connecté : Django affichera sous la réponse le professionnel
    # suggéré par son algorithme d'orientation (jamais par le modèle)
    suggestion_possible: bool = False


class RessourceSuggeree(BaseModel):
    ressource_id: int
    titre: str
    thematique: str


class MessageSortie(BaseModel):
    reponse: str
    source_reponse: str | None
    urgence: bool
    intention: str | None
    ressource: RessourceSuggeree | None
    # Vrai quand la personne cherche un professionnel ou que Titou l'oriente vers
    # l'annuaire : Django ajoute alors la suggestion de son algorithme d'orientation
    orientation_professionnel: bool = False


class RessourceAIndexer(BaseModel):
    id: int
    titre: str
    contenu: str
    thematique: str


def nettoyer(message: str) -> str:
    """Retire les caractères de contrôle et les espaces superflus."""
    sans_controle = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', ' ', message)
    return re.sub(r'\s+', ' ', sans_controle).strip()


def _suggestion(ressource: dict | None) -> RessourceSuggeree | None:
    if not ressource:
        return None
    return RessourceSuggeree(
        ressource_id=ressource['ressource_id'], titre=ressource['titre'], thematique=ressource['thematique']
    )


@app.get('/health')
def health():
    return {'statut': 'ok'}


# Demande explicite d'un professionnel dans le message de la personne
_DEMANDE_PROFESSIONNEL = re.compile(
    r"professionnel|sp[ée]cialiste|psycholog|\bpsy\b|sophrolog|\bcoach|m[ée]diat(eur|rice)|"
    r"assistante? social|mise en relation|parler [àa] quelqu|consulter quelqu|accompagnement",
    re.IGNORECASE,
)


def orientation_vers_professionnel(message: str, reponse: str) -> bool:
    return bool(_DEMANDE_PROFESSIONNEL.search(message)) or 'annuaire' in reponse.lower()


@app.post('/message', response_model=MessageSortie)
def traiter_message(entree: MessageEntree):
    sortie = _repondre(entree)
    # Une réponse d'urgence ne propose que les numéros d'écoute : aucune autre orientation
    if not sortie.urgence:
        sortie.orientation_professionnel = orientation_vers_professionnel(entree.message, sortie.reponse)
    return sortie


def _repondre(entree: MessageEntree) -> MessageSortie:
    message = nettoyer(entree.message)

    # Niveau 0 — sécurité, toujours vérifié en premier
    if detecter_detresse(message):
        return MessageSortie(
            reponse=REPONSE_URGENCE, source_reponse='REGLE', urgence=True, intention=None, ressource=None
        )

    # Niveau 1 — classification d'intention
    resultat = classifier(message)
    intention = resultat.intention if resultat.reconnue_avec_confiance and resultat.intention in REPONSE_PAR_INTENTION else None
    if intention and not generation_disponible():
        return MessageSortie(
            reponse=REPONSE_PAR_INTENTION[intention],
            source_reponse='REGLE',
            urgence=False,
            intention=intention,
            ressource=_suggestion(rechercher(message)),
        )

    # Niveau 2a — ressources validées les plus proches
    ressources = _rechercher_avec_contexte(message, entree.historique)
    meilleure = ressources[0] if ressources else None

    # Niveau 2b — génération encadrée, puis validation
    if generation_disponible():
        texte = _generer_valide(
            message,
            ressources,
            [e.model_dump() for e in entree.historique],
            entree.profil_tendance,
            entree.suggestion_possible,
        )
        if texte:
            return MessageSortie(
                reponse=texte,
                source_reponse='GENERATION',
                urgence=False,
                intention=intention,
                ressource=_suggestion(ressource_evoquee(texte, ressources, _catalogue_ou_rien())),
            )

    # Repli en cascade : réponse prédéfinie, sinon ressource la plus proche, sinon repli
    if intention:
        return MessageSortie(
            reponse=REPONSE_PAR_INTENTION[intention],
            source_reponse='REGLE',
            urgence=False,
            intention=intention,
            ressource=_suggestion(meilleure),
        )
    return MessageSortie(
        reponse=(
            f"Voici une ressource qui pourrait vous aider : « {meilleure['titre']} »."
            if meilleure
            else _repli(entree.historique)
        ),
        source_reponse='RAG',
        urgence=False,
        intention=None,
        ressource=_suggestion(meilleure),
    )


# Un titre d'un seul mot porteur de sens (« Respirer ») se retrouve partout
MOTS_TITRE_MIN = 2


def ressource_evoquee(texte: str, ressources: list[dict], catalogue: list[dict] | None = None) -> dict | None:
    """La ressource que la réponse cite, pour l'encart sous le message.

    Titre cité (tous ses mots porteurs de sens présents), parmi les ressources
    trouvées puis dans tout le catalogue : Titou peut en citer une autre.
    Aucun titre cité : aucun encart. Mieux vaut aucun encart qu'un encart
    hors sujet sous une réponse qui n'en parle pas.
    """
    mots_reponse = mots_significatifs(texte)
    for ressource in [*ressources, *(catalogue or [])]:
        mots_titre = mots_significatifs(ressource['titre'])
        if len(mots_titre) >= MOTS_TITRE_MIN and mots_titre <= mots_reponse:
            return ressource
    return None


# Messages précédents de la personne ajoutés à la recherche : « et je fais
# comment ? » ou « donnez-moi des conseils » ne contiennent aucun sujet
MESSAGES_CONTEXTE_RAG = 2


def _rechercher_avec_contexte(message: str, historique: list[EchangePrecedent]) -> list[dict]:
    """Ressources proches du message seul ET du message replacé dans la conversation.

    Le message seul garde la priorité quand la personne change de sujet ; le
    contexte retrouve le sujet quand le message n'en porte pas.
    """
    trouvees = rechercher_plusieurs(message)
    precedents = [e.contenu for e in historique if e.auteur == 'UTILISATEUR'][-MESSAGES_CONTEXTE_RAG:]
    if precedents:
        deja = {r['ressource_id'] for r in trouvees}
        trouvees += [
            r for r in rechercher_plusieurs(' '.join(precedents + [message])) if r['ressource_id'] not in deja
        ]
    return sorted(trouvees, key=lambda r: -r.get('similarite', 0))[:NOMBRE_MAX_RESULTATS]


def _repli(historique: list[EchangePrecedent]) -> str:
    """Message de repli, différent du dernier envoyé par Titou."""
    dernier = next((e.contenu for e in reversed(historique) if e.auteur == 'BOT'), None)
    return REPONSE_REPLI_BIS if dernier == REPONSE_REPLI else REPONSE_REPLI


def _catalogue_ou_rien() -> list[dict]:
    try:
        return catalogue()
    except Exception:  # le catalogue est un confort : son absence ne bloque jamais la réponse
        journal.warning('Catalogue des ressources indisponible')
        return []


def _generer_valide(
    message: str,
    ressources: list[dict],
    historique: list[dict],
    profil: list[str] | None = None,
    suggestion_possible: bool = False,
) -> str | None:
    """Réponse générée qui a passé le validateur, ou None.

    Mode ressources d'abord s'il y en a ; si sa réponse est rejetée ou vide,
    mode écoute, plutôt que de proposer une ressource qui ne correspond pas.
    Dans chaque mode, une réponse rejetée fait passer au modèle suivant.
    """
    liste = _catalogue_ou_rien()
    precedentes = [e['contenu'] for e in historique if e['auteur'] == 'BOT']
    # Une seule échéance pour toutes les tentatives : Django n'attend jamais trop
    echeance = echeance_totale()

    def accepter_en(mode: str):
        def accepter(texte: str) -> bool:
            validation = valider(texte, ressources, mode, precedentes)
            if not validation.valide:
                # Seule la raison est journalisée, jamais le message ni la réponse
                journal.warning('Réponse générée rejetée (mode %s) : %s', mode, validation.raison)
            return validation.valide

        return accepter

    if ressources:
        texte = generer(
            message,
            ressources,
            historique,
            liste,
            echeance,
            accepter=accepter_en('ressources'),
            profil=profil,
            suggestion_possible=suggestion_possible,
        )
        if texte:
            return texte
    return ecouter(
        message,
        historique,
        liste,
        echeance,
        accepter=accepter_en('ecoute'),
        profil=profil,
        suggestion_possible=suggestion_possible,
    )


@app.post('/reindexer')
def reindexer(ressources: list[RessourceAIndexer]):
    """Appelée par Django (ou le workflow n8n « indexation RAG ») après la
    création ou la modification d'une ressource de la bibliothèque."""
    nombre = indexer_ressources([r.model_dump() for r in ressources])
    return {'ressources_indexees': nombre}
