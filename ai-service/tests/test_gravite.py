"""Nature d'une situation grave : risque vital, violences, détresse."""

import pytest
from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def sans_modele(monkeypatch):
    monkeypatch.setattr(main, 'generer', lambda *a, **k: pytest.fail('modèle appelé sur une situation grave'))
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: pytest.fail('modèle appelé sur une situation grave'))


def envoyer(message):
    return client.post('/message', json={'message': message}).json()


@pytest.mark.parametrize('message', ['Je vais me suicider tout de suite', 'je veux mourir ce soir', 'je veux me tuer'])
def test_un_risque_vital_est_qualifie(message):
    corps = envoyer(message)
    assert (corps['urgence'], corps['nature_detresse']) == (True, 'RISQUE_VITAL')


def test_une_detresse_sans_risque_vital_explicite_reste_une_detresse():
    corps = envoyer("Je n'en peux plus, je ne vois plus d'issue")
    assert (corps['urgence'], corps['nature_detresse']) == (True, 'DETRESSE')


@pytest.mark.parametrize(
    'message',
    ["Mon oncle m'a violée quand j'avais 12 ans", "C'est un inceste, personne ne me croit", 'Mon mari me frappe tous les soirs'],
)
def test_des_violences_subies_ont_une_reponse_dediee_sans_le_modele(message):
    corps = envoyer(message)
    assert (corps['urgence'], corps['nature_detresse']) == (True, 'VIOLENCES')
    assert "vous n'y êtes pour rien" in corps['reponse']
    assert '1515' in corps['reponse']


@pytest.mark.parametrize('message', ['Je joue du violon le soir', 'Ce film était très violent', 'Ma robe violette'])
def test_des_mots_voisins_ne_sont_pas_pris_pour_des_violences(monkeypatch, message):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    assert envoyer(message)['nature_detresse'] is None


@pytest.mark.parametrize('message', ["J'ai envie de tuer mon mari", 'Je vais le tuer ce soir', 'je veux lui faire du mal'])
def test_une_envie_de_tuer_quelqu_un_a_une_reponse_dediee_sans_le_modele(message):
    corps = envoyer(message)
    assert (corps['urgence'], corps['nature_detresse']) == (True, 'DANGER_AUTRUI')
    assert 'éloignez-vous' in corps['reponse']
    assert '800 805 805' in corps['reponse']


@pytest.mark.parametrize('message', ['Je tue le temps en lisant', 'Ce travail me tue', "J'ai tué le moustique"])
def test_des_expressions_courantes_ne_sont_pas_un_danger_pour_autrui(monkeypatch, message):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    assert envoyer(message)['nature_detresse'] is None


def test_un_reseau_bloque_n_empeche_jamais_titou_de_repondre_a_temps(monkeypatch):
    import time as temps

    import app.generateur_reponse as generateur

    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://bloque.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle')
    monkeypatch.setenv('LLM_MODELE', 'modele')
    monkeypatch.delenv('LLM_MODELE_SECOURS', raising=False)
    monkeypatch.setenv('LLM_DELAI_MAX_SECONDES', '1')
    monkeypatch.setenv('LLM_DELAI_TOTAL_SECONDES', '3')

    def reseau_bloque(*args, **kwargs):
        temps.sleep(5)  # résolution d'adresse qui ne rend jamais la main à temps

    monkeypatch.setattr(generateur.httpx, 'post', reseau_bloque)
    debut = temps.monotonic()

    assert generateur.ecouter('bonjour') is None
    assert temps.monotonic() - debut < 3


@pytest.mark.parametrize(
    'message',
    [
        "je vais semer le desordre et alummer le feu de la maison qui m'appartient",
        'Je vais mettre le feu à sa voiture',
        'je vais tout brûler',
        'je vais prendre un couteau',
    ],
)
def test_incendie_destruction_et_armes_sont_des_dangers(message):
    assert envoyer(message)['nature_detresse'] == 'DANGER_AUTRUI'


def test_allumer_le_feu_pour_cuisiner_n_est_pas_un_danger(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    assert envoyer('Je dois allumer le feu pour préparer le thiéboudienne')['nature_detresse'] is None


def historique_de_crise():
    return [
        {'auteur': 'UTILISATEUR', 'contenu': "j'ai envie de tuer mon mari"},
        {'auteur': 'BOT', 'contenu': 'Ce que vous ressentez semble très fort.'},
    ]


def test_une_crise_reste_une_crise_au_message_suivant(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)

    corps = client.post('/message', json={'message': 'non', 'historique': historique_de_crise()}).json()

    assert (corps['urgence'], corps['nature_detresse']) == (True, 'DANGER_AUTRUI')
    assert 'éloigner' in corps['reponse']


def test_en_crise_le_modele_recoit_la_consigne_de_crise(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    recu = {}

    def ecouter_espion(*args, **options):
        recu.update(options)
        return 'Je reste avec vous. Pouvez-vous sortir prendre un peu l’air ?'

    monkeypatch.setattr(main, 'ecouter', ecouter_espion)

    corps = client.post('/message', json={'message': 'non', 'historique': historique_de_crise()}).json()

    assert recu['crise'] is True
    assert corps['reponse'].startswith('Je reste avec vous')
    assert corps['urgence'] is True


def test_apres_quelques_messages_apaises_la_crise_n_est_plus_en_cours():
    historique = historique_de_crise() + [
        {'auteur': 'UTILISATEUR', 'contenu': 'ça va mieux'}, {'auteur': 'BOT', 'contenu': 'Tant mieux.'},
        {'auteur': 'UTILISATEUR', 'contenu': 'je suis calme'}, {'auteur': 'BOT', 'contenu': 'Bien.'},
        {'auteur': 'UTILISATEUR', 'contenu': 'merci'}, {'auteur': 'BOT', 'contenu': 'Avec plaisir.'},
    ]
    assert main.crise_en_cours([main.EchangePrecedent(**e) for e in historique]) is None
