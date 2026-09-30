"""Table de correspondance entre besoins et métiers de la plateforme.

C'est la base de l'algorithme d'orientation : une recommandation doit être
explicable et reproductible, elle ne dépend donc jamais du modèle de langage.
Chaque besoin donne :
- son libellé, repris tel quel dans la phrase d'explication ;
- les métiers qui l'accompagnent, du plus au moins indiqué ;
- des mots repérés dans les domaines déclarés par les professionnels, dans les
  messages de la personne et dans les thématiques des ressources.
"""

from apps.comptes.models import SpecialitePro as M
from apps.suivi.models import TypeEvaluation

BESOINS = {
    'STRESS': {
        'libelle': 'le stress et la tension',
        'metiers': [M.SOPHROLOGUE, M.COACH_DEVELOPPEMENT, M.PSYCHOLOGUE],
        'mots': ['stress', 'tension', 'pression', 'respiration', 'relaxation', 'detente', 'calme'],
    },
    'INQUIETUDE': {
        'libelle': 'les inquiétudes',
        'metiers': [M.PSYCHOLOGUE, M.SOPHROLOGUE],
        'mots': ['inquiet', 'anxi', 'peur', 'angoiss', 'panique'],
    },
    'FATIGUE': {
        'libelle': 'le sommeil et la fatigue',
        'metiers': [M.COACH_SPORTIF, M.SOPHROLOGUE, M.PSYCHOLOGUE],
        'mots': ['sommeil', 'dormir', 'dors', 'insomni', 'nuit', 'fatigue', 'epuis', 'energie', 'activite physique', 'sport'],
    },
    'LIEN_SOCIAL': {
        'libelle': "l'isolement",
        'metiers': [M.PSYCHOLOGUE, M.MEDIATEUR_FAMILIAL],
        'mots': ['isole', 'isolement', 'solitude', 'seul', 'lien social'],
    },
    'FAMILLE': {
        'libelle': 'les relations familiales',
        'metiers': [M.MEDIATEUR_FAMILIAL, M.ASSISTANT_SOCIAL, M.PSYCHOLOGUE],
        'mots': ['famil', 'parent', 'couple', 'conflit', 'communication', 'mariage'],
    },
    'DEMARCHES': {
        'libelle': 'les démarches et la situation sociale',
        'metiers': [M.ASSISTANT_SOCIAL],
        'mots': ['demarche', 'logement', 'administratif', 'aide sociale', 'argent', 'precarite'],
    },
    'TRAVAIL': {
        'libelle': 'la pression au travail',
        'metiers': [M.COACH_DEVELOPPEMENT, M.PSYCHOLOGUE, M.SOPHROLOGUE],
        'mots': ['travail', 'boulot', 'bureau', 'collegue', 'patron', 'echeance', 'deadline', 'carriere', 'emploi', 'organisation'],
    },
    'CONFIANCE': {
        'libelle': 'la confiance en soi',
        'metiers': [M.COACH_DEVELOPPEMENT, M.PSYCHOLOGUE, M.COACH_SPORTIF],
        'mots': ['confiance', 'estime', 'a la hauteur', 'prise de parole', 'timid', 'comparer', 'numerique'],
    },
    'ETUDES': {
        'libelle': 'les études',
        'metiers': [M.PSYCHOLOGUE, M.COACH_DEVELOPPEMENT],
        'mots': ['etude', 'examen', 'revision', 'universit', 'ucad', 'cours', 'etudiant'],
    },
    'DEUIL': {
        'libelle': "la perte d'un proche",
        'metiers': [M.PSYCHOLOGUE],
        'mots': ['deuil', 'deces', 'perte', 'disparu'],
    },
    'EMOTIONS': {
        'libelle': 'les émotions difficiles',
        'metiers': [M.PSYCHOLOGUE, M.SOPHROLOGUE],
        'mots': ['emotion', 'colere', 'rupture', 'relation', 'tristesse', 'pleur'],
    },
    'MOTIVATION': {
        'libelle': 'la motivation',
        'metiers': [M.COACH_DEVELOPPEMENT, M.COACH_SPORTIF],
        'mots': ['motivation', 'envie', 'objectif', 'projet'],
    },
}

# Dimension du test d'auto-évaluation -> besoin
BESOIN_PAR_TEST = {
    TypeEvaluation.STRESS: 'STRESS',
    TypeEvaluation.ANXIETE: 'INQUIETUDE',
    TypeEvaluation.FATIGUE: 'FATIGUE',
}

# Thématique d'une ressource évoquée par le chatbot -> besoin
BESOIN_PAR_THEMATIQUE = {
    'stress': 'STRESS',
    'respiration': 'STRESS',
    'sommeil': 'FATIGUE',
    'travail': 'TRAVAIL',
    'organisation': 'TRAVAIL',
    'famille': 'FAMILLE',
    'lien social': 'LIEN_SOCIAL',
    'confiance en soi': 'CONFIANCE',
    'numérique': 'CONFIANCE',
    'études': 'ETUDES',
    'deuil': 'DEUIL',
    'émotions': 'EMOTIONS',
    'relations': 'EMOTIONS',
    'motivation': 'MOTIVATION',
}

# Quelques mots très courants en wolof : s'ils reviennent dans les messages,
# les professionnels qui parlent wolof passent devant à adéquation égale
MARQUEURS_WOLOF = {
    'dama', 'sama', 'naka', 'nanga', 'def', 'jerejef', 'waaw', 'deedeet', 'xam', 'begg', 'dafa',
    'yangi', 'mangi', 'lool', 'nit', 'dinaa', 'ndax', 'lan', 'lu', 'nekk', 'sonn', 'xel',
}
