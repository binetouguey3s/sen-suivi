"""Niveau 0 du chatbot — sécurité.

Ces expressions déclenchent une réponse d'urgence immédiate, avant toute
classification d'intention ou recherche RAG. La liste vise des expressions
de détresse suicidaire ou de mise en danger, en français courant, avec
leurs variantes sans accent (saisie mobile, autocorrection).

Volontairement statique et modifiable sans redéploiement du reste du
service : dernière mise à jour, à faire évoluer avec un(e) professionnel(le)
si la plateforme grandit.
"""

MOTS_CLES_DETRESSE: list[str] = [
    # Idées suicidaires explicites
    "envie de mourir",
    "envie de me tuer",
    "je veux mourir",
    "je veux me tuer",
    "je vais me tuer",
    "je veux en finir",
    "je veux tout arreter",
    "en finir avec la vie",
    "en finir avec tout",
    "mettre fin a mes jours",
    "mettre fin a ma vie",
    "plus envie de vivre",
    "plus la force de vivre",
    "n'ai plus envie de vivre",
    "je ne veux plus vivre",
    "a quoi bon vivre",
    "la vie ne vaut plus la peine",
    "je pense au suicide",
    "penser au suicide",
    "idees suicidaires",
    "me suicider",
    "suicidaire",
    # Passage à l'acte / moyens (sans jamais citer de méthode : on détecte l'intention, pas le mode opératoire)
    "j'ai prevu de me faire du mal",
    "je vais me faire du mal",
    "je me fais du mal",
    "je m'automutile",
    "me scarifier",
    "me couper pour me soulager",
    # Détresse extrême / désespoir
    "je n'en peux plus",
    "je n'en peux vraiment plus",
    "personne ne me manquera",
    "tout le monde serait mieux sans moi",
    "je suis un fardeau pour tout le monde",
    "je ne vois plus d'issue",
    "il n'y a plus d'espoir pour moi",
]
