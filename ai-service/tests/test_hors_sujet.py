"""Cadrage de Titou : une demande hors du bien-être reçoit un recadrage
prédéfini, sans jamais atteindre le modèle de langage ; un ressenti reste
toujours dans le cadre ; la détresse reste prioritaire. Le modèle et le RAG
sont remplacés par monkeypatch."""

import pytest
from fastapi.testclient import TestClient

import app.generateur_reponse as generateur
import app.main as main
from app.config.hors_sujet import REPONSES_RECADRAGE
from app.detecteur_hors_sujet import detecter_hors_sujet, reponse_recadrage
from app.validateur_reponse import valider

client = TestClient(main.app)

RECADRAGES = {texte for variantes in REPONSES_RECADRAGE.values() for texte in variantes}

HORS_SUJET = [
    'combien font 15 fois 8',
    'résous 2x+3=7',
    'traduis ce texte en anglais',
    'écris-moi une fonction Python',
    'qui a gagné le match hier',
    'donne-moi une recette de thiéboudienne',
]

DANS_LE_CADRE = [
    "j'ai un examen de maths demain et je panique",
    "je n'arrive plus à me concentrer sur mes révisions",
    "c'est quoi la santé mentale ?",
    'comment marche le journal d\'humeur ?',
    'je suis fatigué',
]


def _interdit(*args, **kwargs):
    pytest.fail('modèle de langage appelé pour une demande hors sujet')


@pytest.fixture
def modele_interdit(monkeypatch):
    """Modèle « disponible » mais interdit : un recadrage ne doit jamais l'appeler."""
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'generer', _interdit)
    monkeypatch.setattr(main, 'ecouter', _interdit)
    monkeypatch.setattr(generateur.httpx, 'post', _interdit)
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: pytest.fail('RAG appelé'))


@pytest.fixture
def sans_modele(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'rechercher', lambda message: None)
    monkeypatch.setattr(main, 'catalogue', lambda: [])


def envoyer(message: str, historique: list[dict] | None = None) -> dict:
    reponse = client.post('/message', json={'message': message, 'historique': historique or []})
    assert reponse.status_code == 200
    return reponse.json()


# --- Hors sujet : recadrage, sans le modèle ------------------------------------

@pytest.mark.parametrize('message', HORS_SUJET)
def test_une_demande_hors_sujet_est_recadree_sans_le_modele(modele_interdit, message):
    corps = envoyer(message)
    assert corps['reponse'] in RECADRAGES
    assert corps['source_reponse'] == 'REGLE'
    assert corps['intention'] == 'HORS_SUJET'
    assert corps['urgence'] is False
    assert corps['ressource'] is None
    assert corps['orientation_professionnel'] is False


@pytest.mark.parametrize(
    'message, categorie',
    [
        ('combien font 15 fois 8', 'CALCUL_DEVOIRS'),
        ('15*8 ?', 'CALCUL_DEVOIRS'),
        ('fais mes devoirs de physique', 'CALCUL_DEVOIRS'),
        ('écris-moi une lettre de motivation', 'TACHE'),
        ('quelle est la capitale du Mali ?', 'INFORMATION'),
        ('quel médicament prendre contre le rhume ?', 'CONSEIL_EXPERT'),
        ('tu es ChatGPT ?', 'PERSONNEL'),
        ('tu as combien de tokens ?', 'PERSONNEL'),
    ],
)
def test_la_categorie_choisit_le_recadrage(message, categorie):
    assert detecter_hors_sujet(message) == categorie


def test_deux_recadrages_de_suite_ne_sont_jamais_identiques(modele_interdit):
    premier = envoyer('combien font 15 fois 8')['reponse']
    historique = [
        {'auteur': 'UTILISATEUR', 'contenu': 'combien font 15 fois 8'},
        {'auteur': 'BOT', 'contenu': premier},
    ]
    second = envoyer('et 12 fois 7 ?', historique)['reponse']
    assert second in RECADRAGES and second != premier
    historique += [{'auteur': 'UTILISATEUR', 'contenu': 'et 12 fois 7 ?'}, {'auteur': 'BOT', 'contenu': second}]
    assert envoyer('allez, 3 fois 4', historique)['reponse'] != second


def test_toutes_les_variantes_servies_on_evite_le_dernier_message():
    variantes = REPONSES_RECADRAGE['TACHE']
    assert reponse_recadrage('TACHE', [variantes[1], variantes[0]]) == variantes[1]


# --- Dans le cadre : jamais de recadrage -------------------------------------

@pytest.mark.parametrize('message', DANS_LE_CADRE)
def test_un_message_dans_le_cadre_n_est_pas_recadre(sans_modele, message):
    assert detecter_hors_sujet(message) is None
    corps = envoyer(message)
    assert corps['intention'] != 'HORS_SUJET'
    assert corps['reponse'] not in RECADRAGES


@pytest.mark.parametrize(
    'message',
    [
        "je n'arrive pas à faire mes devoirs, je suis découragée",
        'cette équation me stresse depuis ce matin',
        "j'ai peur de rater ma lettre de motivation",
        'je voudrais seulement parler un peu',
        'je me sens seul ce soir',
    ],
)
def test_une_emotion_l_emporte_sur_la_tache(message):
    assert detecter_hors_sujet(message) is None


@pytest.mark.parametrize('message', ['je voudrais seulement un calcul', 'le calcul de 15 fois 8 seulement'])
def test_seulement_n_est_pas_un_signal_de_solitude(message):
    assert detecter_hors_sujet(message) == 'CALCUL_DEVOIRS'


@pytest.mark.parametrize(
    'message',
    ["je n'ai pas eu ma bourse et je ne sais pas quoi faire", 'ça ne matche pas avec mes collègues', 'bonjour Titou'],
)
def test_pas_de_faux_positif_sur_les_mots_voisins(message):
    assert detecter_hors_sujet(message) is None


# --- La détresse reste prioritaire -------------------------------------------

def test_la_detresse_prime_sur_le_hors_sujet(modele_interdit):
    corps = envoyer('résous 2x+3=7, de toute façon je veux en finir')
    assert corps['urgence'] is True
    assert corps['intention'] is None
    assert '800 805 805' in corps['reponse']


# --- Le validateur rejette une tâche résolue ---------------------------------

@pytest.mark.parametrize(
    'reponse, raison',
    [
        ("Vous êtes sous pression. Pour votre exercice, 2x + 3 = 7 donne x = 2. Bon travail ce soir.", 'calcul'),
        ('Pas de souci, 15 fois 8 font 120. Prenez une pause ensuite.', 'calcul'),
        ('Voici la fonction :\n```python\ndef carre(x):\n    return x * x\n```\nBonne soirée.', 'code'),
        ('Voici la traduction : I am tired and I need to rest with my family for the weekend.', 'anglais'),
    ],
)
def test_le_validateur_rejette_une_tache_resolue(reponse, raison):
    resultat = valider(reponse, [], 'ecoute')
    assert not resultat.valide
    assert raison in resultat.raison


def test_une_consigne_de_respiration_chiffree_reste_acceptee():
    reponse = (
        "La pression des révisions se fait sentir. Essayez d'inspirer sur 4 temps puis d'expirer sur 6 temps, "
        "pendant 5 minutes. Voulez-vous essayer maintenant ?"
    )
    assert valider(reponse, [], 'ecoute').valide
