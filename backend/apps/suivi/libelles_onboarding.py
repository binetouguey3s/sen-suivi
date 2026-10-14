"""Libellés des réponses de l'onboarding de personnalisation.

Mêmes valeurs que frontend/src/app/features/onboarding/onboarding.donnees.ts :
le profil transmis au chatbot parle avec des mots (« étudiant·e »), jamais
avec des codes (« etudiant »). Seuls les champs utiles au chatbot sont repris :
ni genre, ni tranche d'âge, ni spiritualité détaillée, ni « plus à l'aise avec ».
Une valeur absente d'une liste (ancienne version) est simplement ignorée.
"""

SITUATIONS = {
    'eleve': 'collégien·ne ou lycéen·ne',
    'etudiant': 'étudiant·e',
    'emploi': 'en emploi',
    'recherche': 'en recherche d’emploi',
    'entrepreneur': 'entrepreneur·e',
    'autre': 'autre',
}

LANGUES = {
    'fr': 'français',
    'wo': 'wolof',
    'les_deux': 'français et wolof',
}

PREOCCUPATIONS = {
    'stress': 'stress',
    'etudes': 'études et examens',
    'travail': 'travail',
    'sommeil': 'sommeil',
    'emotions': 'émotions',
    'confiance': 'confiance en soi',
    'motivation': 'motivation',
    'famille': 'famille',
    'relations': 'relations',
    'solitude': 'solitude',
    'deuil': 'deuil',
    'organisation': 'organisation',
    'ecrans': 'écrans et réseaux',
    'avenir': 'l’avenir',
}

BIEN_ETRE = {
    'musique': 'musique',
    'spiritualite': 'spiritualité et prière',
    'meditation': 'méditation',
    'respiration': 'respiration',
    'yoga': 'yoga et étirements',
    'sport': 'sport et marche',
    'lecture': 'lecture',
    'ecriture': 'écriture',
    'podcasts': 'podcasts',
    'nature': 'nature et plage',
    'proche': 'parler à un proche',
    'creer': 'créer',
}

MOMENTS = {
    'matin': 'le matin',
    'midi': 'à midi',
    'soir': 'le soir',
    'coucher': 'avant de dormir',
}

DUREES = {
    '2': '2 min',
    '5-10': '5-10 min',
    '15+': '15 min et plus',
}

FORMATS = {
    'texte': 'texte',
    'audio': 'audio',
    'video': 'vidéo',
    'exercice': 'exercice guidé',
}

ECHANGES_PRO = {
    'pas_maintenant': 'pas pour l’instant',
    'plus_tard': 'plus tard',
    'oui': 'oui',
}

# Mêmes codes que SpecialitePro
METIERS = {
    'PSYCHOLOGUE': 'psychologue',
    'ASSISTANT_SOCIAL': 'assistant·e social·e',
    'COACH_DEVELOPPEMENT': 'coach en développement personnel',
    'SOPHROLOGUE': 'sophrologue',
    'MEDIATEUR_FAMILIAL': 'médiateur·rice familial·e',
    'COACH_SPORTIF': 'coach sportif',
}
