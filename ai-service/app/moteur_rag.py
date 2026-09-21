"""Niveau 2 du chatbot : RAG.

Recherche par similarité dans les ressources validées de la plateforme.
Le chatbot ne construit jamais de texte libre à ce niveau : il renvoie la
ressource la plus proche, telle qu'elle existe dans la bibliothèque.
"""

import os

import chromadb

CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/data/chroma')
SEUIL_SIMILARITE_RAG = float(os.environ.get('SEUIL_SIMILARITE_RAG', '0.40'))
NOMBRE_MAX_RESULTATS = 3

_client = None
_collection = None


def _obtenir_collection():
    """Connexion paresseuse : évite d'ouvrir la base au chargement du module
    (utile pour les tests, qui n'ont pas toujours besoin du RAG)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        # Espace cosinus : la distance renvoyée par Chroma devient directement
        # comparable au seuil de similarité (similarite = 1 - distance).
        _collection = _client.get_or_create_collection(
            name='ressources', metadata={'hnsw:space': 'cosine'}
        )
    return _collection


def indexer_ressources(ressources: list[dict]) -> int:
    """(Ré)indexe les ressources fournies (id, titre, contenu, thematique).

    Appelée par POST /reindexer (déclenchable manuellement ou par le workflow
    n8n « indexation RAG » quand une ressource est ajoutée ou modifiée).
    """
    if not ressources:
        return 0
    collection = _obtenir_collection()
    collection.upsert(
        ids=[str(r['id']) for r in ressources],
        documents=[f"{r['titre']}\n{r['contenu']}" for r in ressources],
        metadatas=[
            {'titre': r['titre'], 'thematique': r['thematique'], 'ressource_id': r['id']}
            for r in ressources
        ],
    )
    return len(ressources)


def rechercher(message: str) -> dict | None:
    """La ressource la plus proche du message, si elle dépasse le seuil de similarité."""
    collection = _obtenir_collection()
    if collection.count() == 0:
        return None

    resultats = collection.query(
        query_texts=[message],
        n_results=min(NOMBRE_MAX_RESULTATS, collection.count()),
        include=['metadatas', 'distances'],
    )
    if not resultats['ids'][0]:
        return None

    meilleure_distance = resultats['distances'][0][0]
    similarite = 1 - meilleure_distance
    if similarite < SEUIL_SIMILARITE_RAG:
        return None

    metadonnees = resultats['metadatas'][0][0]
    return {
        'ressource_id': metadonnees['ressource_id'],
        'titre': metadonnees['titre'],
        'thematique': metadonnees['thematique'],
        'similarite': round(similarite, 2),
    }
