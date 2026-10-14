"""Ce que Titou sait de la personne : prénom et profil seulement avec son
accord, réponse fixe sans accord, jamais de recadrage hors sujet à tort.
Cohérence entre le métier cité et la carte suggérée, phrases redites
supprimées. Le modèle et le RAG sont remplacés par monkeypatch."""

import pytest
from fastapi.testclient import TestClient

import app.generateur_reponse as generateur
import app.main as main
from app.detecteur_hors_sujet import detecter_hors_sujet
from app.reponses_profil import REPONSE_PROFIL_SANS_CONSENTEMENT, REPONSE_PROFIL_VISITEUR
from app.validateur_reponse import dedoublonner, valider

client = TestClient(main.app)

AVEC_ACCORD = {
    'personnalisation': True,
    'prenom': 'Awa',
    'suggestion_possible': True,
    'profil_tendance': ['préoccupations : stress, sommeil', 'ce qui fait du bien : musique'],
}


def _interdit(*args, **kwargs):
    pytest.fail('modèle de langage appelé sans accord')


@pytest.fixture(autouse=True)
def isoler(monkeypatch):
    monkeypatch.setattr(main, 'catalogue', lambda: [])
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'rechercher', lambda message: None)
    monkeypatch.setattr(main, 'generer', lambda *a, **k: None)
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: None)
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)


def envoyer(message: str, **champs) -> dict:
    reponse = client.post('/message', json={'message': message, **champs})
    assert reponse.status_code == 200
    return reponse.json()


def modele(texte: str, appels: list | None = None):
    """Doublure du modèle : sa réponse passe par `accepter`, comme la vraie."""

    def repondre(*args, **kwargs):
        if appels is not None:
            appels.append(kwargs)
        accepter = kwargs.get('accepter')
        return texte if accepter is None or accepter(texte) else None

    return repondre


# --- Prénom et profil : seulement avec accord --------------------------------

def test_avec_accord_comment_je_m_appelle_donne_le_prenom():
    corps = envoyer("je m'appelle comment moi ?", **AVEC_ACCORD)
    assert 'Awa' in corps['reponse']
    assert 'Mon profil' in corps['reponse']
    assert corps['intention'] == 'QUESTION_PROFIL'


def test_avec_accord_le_modele_recoit_le_prenom_et_le_profil(monkeypatch):
    appels = []
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'ecouter', modele('Vous vous appelez Awa, et je suis contente de vous revoir.', appels))

    corps = envoyer('Comment je m’appelle ?', **AVEC_ACCORD)

    assert corps['source_reponse'] == 'GENERATION'
    assert appels[0]['prenom'] == 'Awa'
    assert appels[0]['profil'] == AVEC_ACCORD['profil_tendance']


def test_une_reponse_du_modele_qui_ignore_le_prenom_est_rejetee(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'ecouter', modele('Je ne connais pas votre nom, vous ne l’avez pas mentionné.'))

    corps = envoyer("je m'appelle comment moi ?", **AVEC_ACCORD)

    assert corps['source_reponse'] == 'REGLE'
    assert 'Awa' in corps['reponse']


def test_sans_accord_une_phrase_fixe_renvoie_vers_mon_profil(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'ecouter', _interdit)
    monkeypatch.setattr(main, 'generer', _interdit)

    corps = envoyer('Que savez-vous de moi ?', suggestion_possible=True, prenom=None)

    assert corps['reponse'] == REPONSE_PROFIL_SANS_CONSENTEMENT
    assert 'Mon profil' in corps['reponse']
    assert corps['source_reponse'] == 'REGLE'


def test_un_visiteur_apprend_que_titou_ne_sait_rien_de_lui():
    corps = envoyer("comment je m'appelle ?")
    assert corps['reponse'] == REPONSE_PROFIL_VISITEUR


def test_un_prenom_trop_long_est_refuse():
    reponse = client.post('/message', json={'message': 'bonjour', 'prenom': 'A' * 41})
    assert reponse.status_code == 422


def test_le_prenom_arrive_au_modele_comme_consigne():
    messages = generateur._contexte_profil([], 'Awa')
    assert len(messages) == 1
    assert 'Awa' in messages[0]['content']
    assert 'parcimonie' in messages[0]['content']


# --- Jamais hors sujet ---------------------------------------------------------

@pytest.mark.parametrize(
    'message',
    [
        'pourquoi mon profil vous aide à me connaître ?',
        'donc pourquoi vous dites que les infos de mon profil vous permettent de mieux me connaître ?',
        "je m'appelle comment moi ?",
        'que savez-vous de moi ?',
        'que fait Sen Suivi de mes données ?',
    ],
)
def test_une_question_sur_soi_ou_la_plateforme_n_est_jamais_hors_sujet(message):
    assert detecter_hors_sujet(message) is None
    assert envoyer(message)['intention'] != 'HORS_SUJET'


# --- Le texte nomme le même métier que la carte -----------------------------

ORIENTATION_SOPHROLOGUE = (
    "Un sophrologue pourrait vous aider à relâcher cette tension. "
    "Vous trouverez une suggestion juste sous ce message, et tout l'annuaire de Sen Suivi."
)


def test_le_metier_cite_doit_etre_celui_de_la_carte():
    resultat = valider(ORIENTATION_SOPHROLOGUE, [], 'ecoute', controle_metier=True, metier_attendu='Coach sportif')
    assert not resultat.valide
    assert 'Sophrologue' in resultat.raison
    assert valider(ORIENTATION_SOPHROLOGUE, [], 'ecoute', controle_metier=True, metier_attendu='Sophrologue').valide


def test_sans_professionnel_disponible_aucun_metier_n_est_cite():
    assert not valider(ORIENTATION_SOPHROLOGUE, [], 'ecoute', controle_metier=True, metier_attendu=None).valide


def test_la_specialite_de_la_carte_arrive_au_modele():
    assert 'Coach sportif' in generateur._contexte_suggestion(True, 'Coach sportif')[0]['content']
    assert 'sans citer de métier' in generateur._contexte_suggestion(True, None)[0]['content']
    assert generateur._contexte_suggestion(False, 'Coach sportif') == []


def test_une_reponse_qui_cite_un_autre_metier_que_la_carte_n_est_pas_montree(monkeypatch):
    appels = []
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'ecouter', modele(ORIENTATION_SOPHROLOGUE, appels))

    corps = envoyer(
        'Je suis épuisée, vers qui me tourner ?', suggestion_possible=True, specialite_suggeree='Coach sportif'
    )

    assert corps['reponse'] != ORIENTATION_SOPHROLOGUE
    assert appels[0]['specialite'] == 'Coach sportif'


# --- Phrase redite ----------------------------------------------------------

def test_une_phrase_redite_est_supprimee():
    texte = (
        "Vous vivez une période chargée, ce que beaucoup de personnes traversent. "
        "Beaucoup de personnes traversent cela. Voulez-vous en parler ?"
    )
    assert dedoublonner(texte) == (
        "Vous vivez une période chargée, ce que beaucoup de personnes traversent. Voulez-vous en parler ?"
    )


def test_une_phrase_repetee_mot_pour_mot_est_supprimee():
    assert dedoublonner('Je reste là. Je reste là. Prenez votre temps.') == 'Je reste là. Prenez votre temps.'


def test_deux_phrases_differentes_sont_gardees():
    texte = "Beaucoup de personnes traversent cela. « Respirer avant un examen » propose une pause."
    assert dedoublonner(texte) == texte


def test_la_sortie_du_modele_est_dedoublonnee():
    assert generateur._nettoyer_sortie('<think>…</think>Je reste là. Je reste là.') == 'Je reste là.'
