"""Niveau 2a du chatbot : RAG, avec ChromaDB comme base vectorielle.

Recherche par similarité dans les ressources validées de la plateforme.
Ces ressources sont la seule matière que le niveau 2b (génération encadrée)
a le droit d'utiliser ; sans modèle, le chatbot renvoie la plus proche,
telle qu'elle existe dans la bibliothèque.
"""

import hashlib
import os

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/data/chroma')
# Modèle multilingue : le modèle par défaut de ChromaDB ne comprend que l'anglais
EMBEDDING_MODELE = os.environ.get('EMBEDDING_MODELE', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
SEUIL_SIMILARITE_RAG = float(os.environ.get('SEUIL_SIMILARITE_RAG', '0.45'))
NOMBRE_MAX_RESULTATS = int(os.environ.get('NOMBRE_MAX_RESSOURCES', '3'))

_client = None
_collection = None


def _obtenir_collection():
    """Connexion paresseuse : évite d'ouvrir la base au chargement du module
    (utile pour les tests, qui n'ont pas toujours besoin du RAG)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        # Une collection par modèle d'embeddings : des vecteurs de deux modèles
        # différents ne doivent jamais se mélanger. Changer de modèle demande
        # une réindexation (POST /reindexer, ou la commande reindexer_ressources).
        empreinte = hashlib.sha1(EMBEDDING_MODELE.encode()).hexdigest()[:10]
        # Espace cosinus : la distance renvoyée par Chroma devient directement
        # comparable au seuil de similarité (similarite = 1 - distance).
        _collection = _client.get_or_create_collection(
            name=f'ressources_{empreinte}',
            metadata={'hnsw:space': 'cosine', 'modele': EMBEDDING_MODELE},
            embedding_function=SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODELE),
        )
    return _collection


def indexer_ressources(ressources: list[dict]) -> int:
    """Synchronise l'index avec la liste fournie (id, titre, contenu, thematique).

    Les ressources supprimées côté Django disparaissent aussi de l'index :
    appelée par POST /reindexer (workflow n8n « indexation RAG » ou commande
    manuelle) avec la liste complète des ressources.
    """
    collection = _obtenir_collection()
    ids = [str(r['id']) for r in ressources]
    obsoletes = [i for i in collection.get()['ids'] if i not in ids]
    if obsoletes:
        collection.delete(ids=obsoletes)
    if not ressources:
        return 0
    collection.upsert(
        ids=ids,
        documents=[f"{r['titre']}\n{r['contenu']}" for r in ressources],
        metadatas=[
            {'titre': r['titre'], 'thematique': r['thematique'], 'ressource_id': r['id']}
            for r in ressources
        ],
    )
    return len(ressources)


def rechercher_plusieurs(message: str) -> list[dict]:
    """Les ressources les plus proches du message qui dépassent le seuil de
    similarité, de la plus proche à la moins proche, avec leur contenu :
    c'est la seule matière que le modèle de langage a le droit d'utiliser."""
    collection = _obtenir_collection()
    if collection.count() == 0:
        return []

    resultats = collection.query(
        query_texts=[message],
        n_results=min(NOMBRE_MAX_RESULTATS, collection.count()),
        include=['metadatas', 'distances', 'documents'],
    )
    trouvees = []
    for metadonnees, distance, document in zip(
        resultats['metadatas'][0], resultats['distances'][0], resultats['documents'][0]
    ):
        similarite = 1 - distance
        if similarite < SEUIL_SIMILARITE_RAG:
            continue
        trouvees.append(
            {
                'ressource_id': metadonnees['ressource_id'],
                'titre': metadonnees['titre'],
                'thematique': metadonnees['thematique'],
                'contenu': document,
                'similarite': round(similarite, 2),
            }
        )
    return trouvees


def catalogue() -> list[dict]:
    """Titre et thématique de toutes les ressources indexées : Titou peut ainsi
    citer d'autres ressources de la bibliothèque quand on les lui demande
    (l'identifiant sert seulement à l'encart sous le message)."""
    collection = _obtenir_collection()
    return sorted(
        (
            {'ressource_id': m['ressource_id'], 'titre': m['titre'], 'thematique': m['thematique']}
            for m in collection.get(include=['metadatas'])['metadatas']
        ),
        key=lambda r: (r['thematique'], r['titre']),
    )


def rechercher(message: str) -> dict | None:
    """La ressource la plus proche du message, si elle dépasse le seuil de similarité."""
    trouvees = rechercher_plusieurs(message)
    if not trouvees:
        return None
    meilleure = trouvees[0]
    return {cle: meilleure[cle] for cle in ('ressource_id', 'titre', 'thematique', 'similarite')}
