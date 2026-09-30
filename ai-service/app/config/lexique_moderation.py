"""Lexique du niveau 0 de la modération du forum (règles, sans modèle).

Principe directeur : on bloque l'AGRESSION, jamais la SOUFFRANCE. Ce niveau ne
traite donc que les cas évidents ; tout ce qui est ambigu passe au modèle.

Tous les termes sont écrits sous forme normalisée : minuscules, sans accents,
lettres répétées réduites à une seule (« connard » s'écrit « conard »). Le
texte du message subit la même normalisation avant comparaison, ce qui déjoue
les contournements courants (C0NNARD, c.o.n.n.a.r.d, connaaaard…).
"""

# Insultes sans ambiguïté, en français et en wolof : bloquées dès qu'elles
# apparaissent, sauf dans un récit (« on me traitait de … »), qui part au modèle
INSULTES_FORTES = [
    # français
    'conard', 'conase', 'salope', 'salaud', 'pute', 'putain de ta', 'encule', 'fils de pute', 'fdp',
    'ntm', 'nique ta mere', 'nique ta race', 'ta gueule', 'ferme ta gueule', 'pede', 'batard',
    'sale chien', 'grosse vache', 'tocard', 'va te faire', 'trou du cul',
    # wolof
    'domu aram', 'saga ndey', 'kacor',
]

# Mots ambigus : une insulte seulement quand ils visent quelqu'un (« t'es un
# idiot », « espèce de dof »). Seuls, ils décrivent souvent ce qu'on ressent
# soi-même (« je me sens idiote ») et ne sont jamais bloqués.
INSULTES_CIBLEES = [
    'con', 'cone', 'idiot', 'idiote', 'debile', 'cretin', 'cretine', 'abruti', 'abrutie', 'imbecile',
    'nul', 'nule', 'minable', 'rate', 'bouffon', 'clown', 'moche', 'grosse', 'gros porc',
    # wolof
    'dof', 'mbam', 'xaj', 'ciif', 'saay saay', 'dofe',
]

# Ce qui fait d'un mot ambigu une attaque : il est adressé à quelqu'un
MARQUEURS_CIBLAGE = [
    "t'es", 'tu es', 't es', 'vous etes', 'espece de', 'espece d', 'bande de', 'pauvre',
    "t'as vu", 'regardez moi ce', 'yow', 'yaw', 'yangi', 'danga', 'dangay',
]

# Ce qui fait d'une insulte un récit : la personne rapporte ce qu'elle a subi
MARQUEURS_RECIT = [
    'me trait', 'm ont trait', 'm a trait', 'nous trait', 'la trait', 'le trait', 'traite de', 'traitait de',
    'm appel', 'm ont appel', 'on m appel', 'me disai', 'me dis', 'm a dit', 'm ont dit', 'm insult',
    'surnom', 'on me', 'ils me', 'elle me', 'il me', 'mon mari me', 'ma mere me', 'mon pere me',
    'se moqu', 'harcel',
]

# Réseaux sociaux et messageries : partager un compte expose la personne
RESEAUX_SOCIAUX = [
    'instagram', 'insta', 'snapchat', 'snap', 'facebook', 'tiktok', 'whatsapp', 'whatsap', 'telegram',
    'twitter', 'linkedin', 'messenger',
]

# Sollicitations commerciales
SPAM = [
    'code promo', 'promo', 'reduction de', 'gagnez', 'cliquez', 'achetez', 'offre speciale',
    'crypto', 'bitcoin', 'forex', 'investissement garanti', 'gagner de l argent', 'argent facile',
    'devenez riche', 'contactez moi pour', 'vente de', 'je vends', 'livraison gratuite', 'abonnez vous',
]

# Numéros utiles qu'on a le droit de partager sur le forum
NUMEROS_AUTORISES = {'800805805', '1515', '18'}
