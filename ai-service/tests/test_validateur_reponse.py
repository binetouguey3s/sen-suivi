"""Validateur de sortie du niveau 2b : une réponse qui enfreint une règle de
ton ou de fond n'est jamais montrée à l'utilisateur."""

import pytest

from app.validateur_reponse import valider

RESSOURCES = [{'ressource_id': 1, 'titre': 'Respirer avant un examen', 'thematique': 'Respiration', 'contenu': '…'}]

REPONSE_CORRECTE = (
    "Vous sentez la pression monter à l'approche de vos examens. Beaucoup de personnes "
    "traversent cela en fin d'année. La ressource « Respirer avant un examen » propose "
    "cinq minutes de respiration lente à faire avant l'épreuve. Voulez-vous l'essayer ce soir ?"
)


def test_une_reponse_conforme_est_acceptee():
    assert valider(REPONSE_CORRECTE, RESSOURCES).valide


# --- Les 8 formules creuses ---------------------------------------------------

@pytest.mark.parametrize(
    'formule',
    [
        'Je comprends ce que vous vivez.',
        'Je vous comprends tout à fait.',
        'Je suis désolé pour vous.',
        'Je suis désolée de lire cela.',
        "C'est normal de se sentir ainsi.",
        'Courage, cela va passer.',
        'Restez positif malgré tout.',
        'Restez positive, vous y arriverez.',
    ],
)
def test_une_formule_creuse_est_rejetee(formule):
    resultat = valider(f'{formule} La ressource « Respirer » peut vous aider.', RESSOURCES)
    assert not resultat.valide
    assert resultat.raison.startswith('formule creuse')


@pytest.mark.parametrize('exhortation', ['Bon courage pour la suite.', 'Gardez courage.', 'Vous y arriverez, courage !'])
def test_une_exhortation_au_courage_est_rejetee(exhortation):
    assert valider(exhortation, RESSOURCES).raison.startswith('formule creuse')


def test_reprendre_le_mot_courage_de_la_personne_est_permis():
    reponse = 'Ce manque de courage que vous décrivez pèse sur vos journées. Voulez-vous m’en dire plus ?'
    assert valider(reponse, RESSOURCES).valide


def test_encourager_n_est_pas_confondu_avec_courage():
    reponse = "Cette ressource peut vous encourager à faire une pause. Voulez-vous la lire ?"
    assert valider(reponse, RESSOURCES).valide


# --- Règles de fond -----------------------------------------------------------

def test_une_reponse_sans_ressource_est_rejetee():
    resultat = valider(REPONSE_CORRECTE, [])
    assert not resultat.valide
    assert resultat.raison == 'réponse générée sans ressource'


@pytest.mark.parametrize(
    'phrase',
    [
        'Ce trouble du sommeil est fréquent.',
        'Une thérapie pourrait vous aider.',
        'Ce ne sont que des symptômes passagers.',
        'Un médicament pour dormir peut aider.',
        'Cela ressemble à une dépression.',
    ],
)
def test_un_terme_clinique_est_rejete(phrase):
    resultat = valider(phrase, RESSOURCES)
    assert not resultat.valide
    assert resultat.raison.startswith('terme clinique')


def test_le_tutoiement_est_rejete():
    assert valider("Tu peux essayer la respiration lente ce soir.", RESSOURCES).raison == 'tutoiement'


def test_plus_de_quatre_phrases_est_rejete():
    reponse = 'Une phrase. Une deuxième. Une troisième. Une quatrième. Une cinquième.'
    assert valider(reponse, RESSOURCES).raison == 'plus de 4 phrases'


def test_une_liste_a_puces_est_rejetee():
    reponse = "Voici quelques idées :\n- respirer lentement\n- marcher un peu."
    assert valider(reponse, RESSOURCES).raison == 'liste à puces'


def test_question_et_proposition_multiples_rejetees():
    reponse = 'Comment dormez-vous ? Et le matin, comment vous sentez-vous ?'
    assert valider(reponse, RESSOURCES).raison == "plus d'une question"


def test_un_numero_non_autorise_est_rejete():
    resultat = valider('Appelez le 77 123 45 67 pour en parler.', RESSOURCES)
    assert not resultat.valide
    assert resultat.raison.startswith('numéro non autorisé')


def test_les_numeros_d_ecoute_et_les_petits_nombres_sont_acceptes():
    reponse = "Le 800 805 805 et le 1515 répondent à toute heure. Prenez 5 minutes pour respirer."
    assert valider(reponse, RESSOURCES).valide


def test_une_mention_de_tarif_est_rejetee():
    resultat = valider("Le tarif d'une séance est indiqué sur le profil.", RESSOURCES)
    assert resultat.raison.startswith('sujet payant')


def test_une_promesse_de_guerison_est_rejetee():
    resultat = valider('Avec cet exercice, vous allez guérir.', RESSOURCES)
    assert resultat.raison.startswith('promesse interdite')


def test_une_reponse_qui_repete_la_precedente_est_rejetee():
    precedente = REPONSE_CORRECTE
    reprise = REPONSE_CORRECTE.replace('ce soir', 'maintenant')
    assert valider(reprise, RESSOURCES, precedentes=[precedente]).raison == "répétition d'une réponse précédente"


def test_une_reponse_differente_de_la_precedente_est_acceptee():
    precedente = "Bonjour, je suis Titou, l'assistant d'écoute de Sen Suivi. Comment vous sentez-vous aujourd'hui ?"
    assert valider(REPONSE_CORRECTE, RESSOURCES, precedentes=[precedente]).valide


@pytest.mark.parametrize('coupee', ['Je vous propose une', "Vous pouvez consulter l'annuaire pour demander une mise", 'Je'])
def test_une_reponse_inachevee_est_rejetee(coupee):
    assert valider(coupee, RESSOURCES, 'ecoute').raison == 'réponse inachevée'


@pytest.mark.parametrize('fin', ['Voulez-vous essayer ?', 'Je reste là.', 'Lisez « Respirer avant un examen ».', 'Vous y êtes presque !'])
def test_une_reponse_qui_finit_sa_phrase_est_acceptee(fin):
    assert valider(fin, RESSOURCES, 'ecoute').valide
