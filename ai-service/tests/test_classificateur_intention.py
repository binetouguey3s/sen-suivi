from app.classificateur_intention import classifier


def test_stress_reconnu_avec_confiance():
    resultat = classifier("Je suis stressé par mes examens, j'angoisse beaucoup.")
    assert resultat.intention == 'STRESS'
    assert resultat.reconnue_avec_confiance is True


def test_fatigue_reconnue_avec_confiance():
    resultat = classifier("Je dors mal depuis une semaine, je n'arrive pas à dormir.")
    assert resultat.intention == 'FATIGUE'
    assert resultat.reconnue_avec_confiance is True


def test_message_ambigu_non_reconnu():
    resultat = classifier("Bonjour, comment ça va ?")
    assert resultat.reconnue_avec_confiance is False
