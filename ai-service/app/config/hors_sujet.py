"""Cadrage de Titou : ce qui sort du bien-être et de l'usage de Sen Suivi.

Liste de configuration, comme les mots-clés de détresse : on l'enrichit ici
sans toucher au détecteur. Toutes les expressions sont écrites sans accents et
en minuscules, car la comparaison se fait sur un texte normalisé.

La comparaison se fait mot par mot : « seul » ne se déclenche pas dans
« seulement ». Une expression terminée par * est une racine : « tradui* »
attrape « traduis », « traduire » et « traduisez ».

Règle principale : un signal de bien-être ou une mention de la plateforme
l'emporte toujours. « J'ai un examen de maths demain et je panique » reste
dans le cadre : on répond à l'émotion, jamais à l'exercice.
"""

# Ce que la personne ressent ou vit : le message reste dans le cadre
SIGNAUX_BIEN_ETRE = [
    'stress*', 'angoiss*', 'anxi*', 'panique*', 'paniquer', 'peur', 'inquiet*', 'inquiete*', 'nerveu*',
    'pression', 'fatigu*', 'epuis*', 'dormir', 'dors', 'sommeil', 'decourag*', 'demotiv*', 'ma motivation',
    'manque de motivation', 'plus de motivation', 'pas de motivation',
    'triste*', 'tristesse', 'pleur*', 'seul', 'seule', 'seuls', 'seules', 'solitude', 'colere', 'honte',
    'confiance en moi', 'je me sens', "j'ai du mal", "je n'arrive pas", "je n'arrive plus", "j'arrive pas",
    "j'arrive plus", 'ca ne va pas', 'ca va pas', 'ca me pese', 'moral', 'deuil', 'deprime*', 'mal-etre',
    'mal etre', 'bien-etre', 'bien etre', 'sante mentale', 'emotion*', 'ressens', 'ressenti',
]

# Ce que propose Sen Suivi : une question sur la plateforme est toujours dans le cadre
MENTIONS_PLATEFORME = [
    'titou', 'sen suivi', 'journal d\'humeur', 'mon journal', 'auto-evaluation*', 'autoevaluation*',
    'bibliotheque', 'forum', 'annuaire', 'professionnel*', 'mise en relation', 'confidentialite',
    'parametres', 'numero d\'urgence', 'numeros d\'urgence', 'lieux de detente', 'lieu de detente',
    # La personne, son profil et ses données : toujours dans le cadre
    'mon profil', 'mes informations', 'mes infos', 'mes donnees', 'donnees personnelles', 'mon prenom',
    "comment je m'appelle", "je m'appelle comment", 'que savez vous de moi', 'que sais tu de moi',
    'savez sur moi', 'sais sur moi', 'me connaitre', 'me connaissez', 'me connais', 'plateforme',
]

# Demandes de tâche ou d'information, par catégorie : la catégorie choisit le recadrage
MOTIFS_HORS_SUJET: dict[str, list[str]] = {
    'CALCUL_DEVOIRS': [
        'combien font', 'combien fait', 'calcul*', 'resous', 'resoudre', 'resolvez', 'equation*', 'derivee*',
        'integrale*', 'racine carree', 'fais mes devoirs', 'fais mon devoir', 'faire mes devoirs a ma place',
        'dissertation', 'expose sur', 'commentaire compose', 'corrige mon', 'corrige ma', 'corrige mes',
        'corrige ce', 'corrige cette', 'corrigez mon', 'corrigez ce',
    ],
    'TACHE': [
        'tradui*', 'traduction', 'en anglais', 'en espagnol', 'python', 'javascript', 'java', 'sql', 'html',
        'css', 'php',
        'ecris-moi un code', 'ecris moi un code', 'ecris un code', 'ecris-moi une fonction', 'ecris une fonction',
        'ecris-moi un script', 'ecris un script', 'ecris-moi un programme', 'ecris un programme', 'algorithme*',
        'ecris-moi une lettre', 'ecris moi une lettre', 'ecris une lettre', 'lettre de motivation', 'cv',
        'curriculum', 'redige-moi', 'redige moi', 'redigez-moi', 'resume ce texte', 'resume-moi ce',
    ],
    'INFORMATION': [
        'capitale de', 'capitale du', 'capitale des', 'qui a invente', 'qui a ecrit', 'en quelle annee',
        'definition de', 'definition du', 'definition des', 'la definition',
        'actualite*', 'les infos', 'derniere nouvelle', 'dernieres nouvelles', 'meteo', 'quel temps fait',
        'va-t-il pleuvoir', 'va pleuvoir', 'match', 'qui a gagne', "ballon d'or",
        'coupe du monde', 'ligue des champions', 'championnat', 'recette*', 'cuisiner', 'ingredients',
        'election*', 'parti politique', 'president de la republique', 'gouvernement', 'ministre', 'quelle religion',
        'dieu existe',
    ],
    'CONSEIL_EXPERT': [
        'quel medicament', 'quels medicaments', 'medicament pour', 'posologie', 'quelle dose', 'antibiotique*',
        'paracetamol', 'doliprane', 'ordonnance', 'conseil juridique', 'avocat', 'droit du travail', 'investir',
        'en bourse', 'crypto*', 'bitcoin', 'placement financier', "taux d'interet", 'pret bancaire',
    ],
    'PERSONNEL': [
        'quel modele', 'chatgpt', 'openai', "qui t'a cree", "qui t'a programme", "qui t'a concu",
        "qui vous a cree", 'qui vous a programme',
        'tokens', 'token', 'jetons', 'ton prompt', 'votre prompt',
    ],
}

# Opérations chiffrées, sur le texte normalisé : « 15*8 », « 2x+3=7 », « 15 fois 8 »
OPERATIONS_CHIFFREES = [
    r'\d\s*[+*×÷=^]\s*\d',
    r'\d\s*x\s*[-+=]',
    r'\d+\s*(?:fois|plus|moins|divise par|multiplie par)\s*\d',
]

# Recadrages : chacun reconnaît la demande sans la traiter, rappelle ce que
# Titou peut faire et propose une porte d'entrée. Jamais le mot « annuaire » :
# il ferait afficher une suggestion de professionnel sous un simple recadrage.
REPONSES_RECADRAGE: dict[str, list[str]] = {
    'CALCUL_DEVOIRS': [
        "Je ne suis pas fait pour les calculs ni pour les devoirs, mais je peux vous aider à gérer la pression "
        "des révisions ou à trouver un moment pour souffler. Comment vous sentez-vous en ce moment ?",
        "Résoudre des exercices, ce n'est pas mon rôle : je suis là pour ce que vous vivez. Si les études pèsent "
        "en ce moment, la bibliothèque de Sen Suivi propose des ressources pour réviser sans s'épuiser. "
        "Qu'est-ce qui vous occupe le plus l'esprit aujourd'hui ?",
    ],
    'TACHE': [
        "Écrire, traduire ou programmer, ce n'est pas ce que je sais faire : je suis là pour votre bien-être. "
        "Si cette tâche vous met sous pression, on peut en parler, ou chercher ensemble un moyen de souffler. "
        "Comment ça se passe pour vous en ce moment ?",
        "Je ne rédige pas, je ne traduis pas et je n'écris pas de code, mais je peux vous écouter, et le journal "
        "d'humeur de Sen Suivi vous aide à faire le point sur vos journées. Comment vous sentez-vous aujourd'hui ?",
    ],
    'INFORMATION': [
        "Je ne suis pas la bonne source pour ce genre d'information : mon rôle, c'est de vous accompagner dans "
        "ce que vous vivez. Si vous avez besoin de souffler, les lieux de détente de Sen Suivi peuvent vous "
        "donner des idées. Comment allez-vous en ce moment ?",
        "Là-dessus, je ne peux pas vous renseigner : je suis là pour parler de vous et de votre bien-être. "
        "Vous pouvez aussi échanger avec d'autres personnes sur le forum de Sen Suivi. "
        "Qu'est-ce qui vous amène aujourd'hui ?",
    ],
    'CONSEIL_EXPERT': [
        "Pour une question de santé, de droit ou d'argent, mieux vaut vous adresser à quelqu'un dont c'est le "
        "métier : un médecin, un pharmacien, un juriste ou un conseiller. De mon côté, je peux vous écouter si "
        "cette situation vous préoccupe. Comment la vivez-vous ?",
        "Ce type de conseil demande un spécialiste, et je ne veux pas risquer de vous induire en erreur. "
        "Si cette question vous inquiète, je suis là pour en parler avec vous.",
    ],
    'PERSONNEL': [
        "Je suis Titou, l'assistant d'écoute de Sen Suivi, et c'est tout ce qu'il y a à savoir sur moi. "
        "Parlons plutôt de vous : comment vous sentez-vous aujourd'hui ?",
        "Je préfère laisser la place à ce que vous vivez : c'est vous qui comptez dans cette conversation. "
        "Comment allez-vous en ce moment ?",
    ],
}
