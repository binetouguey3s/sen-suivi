"""Test minimal requis par docs/CONTEXTE.md section 7 : détection de détresse.

Le niveau 0 est une fonctionnalité de sécurité : un faux négatif (une
détresse réelle non détectée) est le risque le plus grave du projet.
"""

from app.detecteur_detresse import detecter_detresse


def test_detecte_une_phrase_explicite():
    assert detecter_detresse("Je veux en finir, je n'en peux plus.") is True


def test_detecte_sans_accents_ni_majuscules():
    assert detecter_detresse("JE VEUX MOURIR, plus rien n'a de sens") is True


def test_detecte_au_milieu_d_un_message_plus_long():
    message = (
        "Bonjour, je ne sais pas trop comment dire ça mais depuis quelques jours "
        "j'ai des idees suicidaires et ça m'inquiète beaucoup."
    )
    assert detecter_detresse(message) is True


def test_ignore_un_message_de_stress_ordinaire():
    assert detecter_detresse("Je suis stressé par mes examens en ce moment.") is False


def test_ignore_un_message_de_fatigue_ordinaire():
    assert detecter_detresse("Je dors mal depuis quelques jours, j'aimerais des conseils.") is False


def test_message_vide():
    assert detecter_detresse('') is False
