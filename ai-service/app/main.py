"""Microservice IA (FastAPI), séparé du back-end Django (docs/CONTEXTE.md section 2).

Trois niveaux, toujours dans cet ordre :
1. Détection de détresse (sécurité) — si déclenchée, on s'arrête là.
2. Classification d'intention — réponse validée prédéfinie si reconnue avec confiance.
3. RAG — recherche par similarité dans les ressources vectorisées, sinon repli.

Jamais de LLM génératif libre : chaque réponse vient soit d'un texte validé
prédéfini, soit d'une ressource existante de la plateforme.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.classificateur_intention import REPONSE_PAR_INTENTION, classifier
from app.detecteur_detresse import REPONSE_URGENCE, detecter_detresse
from app.moteur_rag import indexer_ressources, rechercher

REPONSE_REPLI = (
    "Je n'ai pas de ressource précise à ce sujet pour le moment. Vous pouvez "
    "explorer la bibliothèque de ressources de Sen Suivi ou demander une mise "
    "en relation avec un professionnel."
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


class MessageEntree(BaseModel):
    message: str


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


class RessourceAIndexer(BaseModel):
    id: int
    titre: str
    contenu: str
    thematique: str


@app.get('/health')
def health():
    return {'statut': 'ok'}


@app.post('/message', response_model=MessageSortie)
def traiter_message(entree: MessageEntree):
    message = entree.message.strip()

    # Niveau 0 — sécurité, toujours vérifié en premier
    if detecter_detresse(message):
        return MessageSortie(
            reponse=REPONSE_URGENCE, source_reponse='REGLE', urgence=True, intention=None, ressource=None
        )

    # Niveau 1 — classification d'intention
    resultat = classifier(message)
    if resultat.reconnue_avec_confiance and resultat.intention in REPONSE_PAR_INTENTION:
        ressource_trouvee = rechercher(message)
        return MessageSortie(
            reponse=REPONSE_PAR_INTENTION[resultat.intention],
            source_reponse='REGLE',
            urgence=False,
            intention=resultat.intention,
            ressource=RessourceSuggeree(**ressource_trouvee) if ressource_trouvee else None,
        )

    # Niveau 2 — RAG, sinon repli
    ressource_trouvee = rechercher(message)
    if ressource_trouvee:
        reponse = f"Voici une ressource qui pourrait vous aider : « {ressource_trouvee['titre']} »."
    else:
        reponse = REPONSE_REPLI
    return MessageSortie(
        reponse=reponse,
        source_reponse='RAG',
        urgence=False,
        intention=None,
        ressource=RessourceSuggeree(**ressource_trouvee) if ressource_trouvee else None,
    )


@app.post('/reindexer')
def reindexer(ressources: list[RessourceAIndexer]):
    """Appelée par Django (ou le workflow n8n « indexation RAG ») après la
    création ou la modification d'une ressource de la bibliothèque."""
    nombre = indexer_ressources([r.model_dump() for r in ressources])
    return {'ressources_indexees': nombre}
