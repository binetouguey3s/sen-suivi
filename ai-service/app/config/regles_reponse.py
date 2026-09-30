"""Règles que toute réponse générée par le modèle de langage doit respecter.

Liste de configuration, comme les mots-clés de détresse : on l'enrichit ici
sans toucher au code du validateur. Toutes les expressions sont écrites sans
accents et en minuscules, car la comparaison se fait sur un texte normalisé.

La comparaison se fait mot par mot, pluriel et féminin compris : « courage »
ne se déclenche pas dans « encourager ». Une expression terminée par * est une
racine : « therapeut* » attrape « thérapeute » et « thérapeutique ».
"""

# Formules creuses : elles donnent l'illusion de l'écoute sans rien accueillir
FORMULES_CREUSES = [
    'je comprends',
    'je vous comprends',
    'je suis desole',
    'je suis desolee',
    "c'est normal",
    'bon courage',
    'courage a vous',
    'gardez courage',
    'restez positif',
    'restez positive',
    'ce n\'est pas grave',
    'ca va aller',
    'il y a pire',
    'vous devriez ressentir',
]

# Vocabulaire clinique : Sen Suivi parle de bien-être, jamais de soin
TERMES_CLINIQUES = [
    'patient',
    'trouble',
    'therapie',
    'therapeut*',
    'diagnostic',
    'diagnostiqu*',
    'pathologi*',
    'maladie',
    'depression',
    'bipolaire',
    'schizophren*',
    'symptome',
    'medicament',
    'posologie',
    'antidepresseur',
    'anxiolytique',
    'somnifere',
    'ordonnance',
    'traitement',
]

# Promesses de guérison et substitution à un professionnel
PROMESSES_INTERDITES = [
    'guerir',
    'guerison',
    'vous allez aller mieux',
    'pas besoin de consulter',
    'pas besoin d\'un professionnel',
    'je remplace',
]

# Mots interdits seulement quand ils servent d'exhortation : en début de
# phrase ou suivis d'un point d'exclamation (« Courage ! », « Courage, ça va
# passer »). Les reprendre dans une reformulation (« votre manque de courage »)
# reste permis : c'est souvent le mot de la personne elle-même.
EXHORTATIONS = ['courage']

# Aucun sujet d'argent dans le chatbot
TERMES_PAYANTS = [
    'abonnement',
    'formule payante',
    'payant',
    'tarif',
    'prix',
    'fcfa',
    'paiement',
]

# Seuls numéros autorisés dans une réponse (chiffres sans espaces)
NUMEROS_AUTORISES = {'800805805', '1515', '18'}

# Une réponse longue n'est pas une réponse attentionnée
PHRASES_MAX = 4
# Mode écoute (aucune ressource) : on accueille, on ne développe pas
PHRASES_MAX_ECOUTE = 3

# Au-delà de cette part de mots communs avec un message précédent de Titou,
# la réponse est une répétition : une conversation qui tourne en rond n'écoute plus
SIMILARITE_REPETITION_MAX = 0.7

# Mots trop courants pour dire de quoi parle un texte : ignorés quand on compare
# deux textes (répétition, ressource évoquée par une réponse)
MOTS_VIDES = {
    'vous', 'votre', 'vos', 'nous', 'notre', 'pour', 'dans', 'avec', 'sans', 'sous', 'chez', 'entre',
    'plus', 'moins', 'tres', 'bien', 'aussi', 'encore', 'ainsi', 'alors', 'mais', 'donc', 'comme',
    'cette', 'cela', 'ceci', 'celle', 'celui', 'ceux', 'elle', 'elles', 'leur', 'leurs', 'meme',
    'tout', 'tous', 'toute', 'toutes', 'quand', 'quoi', 'dont', 'etre', 'avoir', 'fait', 'faire',
    'peut', 'peuvent', 'pouvez', 'voulez', 'souhaitez', 'sont', 'etes', 'avez', 'suis', 'avait',
    'beaucoup', 'personnes', 'chose', 'choses', 'quelque', 'moment', 'parfois', 'souvent',
}
QUESTIONS_MAX = 1
