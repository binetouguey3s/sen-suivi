"""Nature d'une situation grave, pour adapter l'aide (sans modifier le niveau 0).

Le détecteur de détresse (detecteur_detresse.py, mots_cles_detresse.py) reste
intact et prioritaire. Cette liste ne sert qu'à QUALIFIER la situation :
- RISQUE_VITAL : la personne exprime un risque pour sa vie. Avec son accord
  préalable, sa personne de confiance peut être prévenue automatiquement.
- DANGER_AUTRUI : la personne exprime l'envie de tuer ou de blesser quelqu'un,
  de mettre le feu, de tout détruire, ou parle d'une arme.
  Réponse calme, sans jugement, numéros et professionnel. JAMAIS d'alerte
  automatique à un proche : il peut être la personne visée.
- VIOLENCES : la personne révèle des violences subies (sexuelles, intrafamiliales,
  physiques). JAMAIS d'alerte automatique à un proche : l'agresseur peut en faire
  partie. Réponse dédiée, numéros, professionnel adapté.

Expressions normalisées (minuscules, sans accents), cherchées comme mots
entiers ; « * » final = racine (« suicid* » : suicide, suicidaire…). À faire
valider par des professionnels de santé et des associations partenaires.
"""

RISQUE_VITAL: list[str] = [
    'suicid*', 'me tuer', 'me donner la mort', 'mourir', 'en finir', 'mettre fin a mes jours',
    'mettre fin a ma vie', 'plus envie de vivre', 'ne veux plus vivre', 'me faire du mal',
    'm automutil*', 'me scarifier', 'me pendre',
]

DANGER_AUTRUI: list[str] = [
    'tuer mon', 'tuer ma', 'tuer mes', 'tuer son', 'tuer sa', 'tuer ses', 'tuer quelqu*', 'tuer tout le monde',
    'le tuer', 'la tuer', 'les tuer', 'te tuer', 'vous tuer', 'tuer cet*', 'tuer ce',
    'lui faire du mal', 'leur faire du mal', 'faire du mal a mon', 'faire du mal a ma', 'faire du mal a mes',
    'le frapper a mort', 'la frapper a mort', 'poignarder', 'egorger', 'massacrer',
    # Incendie, destruction, armes
    'mettre le feu', 'mettre feu', 'allumer le feu a', 'allumer le feu de', 'allumer le feu dans', 'bruler la maison',
    'bruler ma maison', 'bruler sa maison', 'bruler leur maison', 'tout bruler', 'incendi*', 'faire exploser',
    'tout casser', 'tout detruire', 'prendre un couteau', 'avec un couteau', 'prendre une arme', 'acheter une arme',
    'mon arme', 'un fusil', 'mon fusil', 'un pistolet', 'empoisonner',
]

# Deux mots qui, ensemble, signalent un danger (« le feu … la maison »)
COMBINAISONS_DANGER: list[tuple[str, tuple[str, ...]]] = [
    ('feu', ('maison', 'chambre', 'appartement', 'voiture', 'quartier', 'tout', 'desordre')),
    ('couteau', ('tuer', 'frapper', 'blesser', 'planter')),
]

VIOLENCES: list[str] = [
    'viol', 'viols', 'violee', 'violer', 'viole', 'inceste', 'incestueu*', 'abus sexuel*', 'abusee sexuellement',
    'agression sexuelle', 'agresse sexuellement', 'agressee sexuellement', 'attouchement*', 'me touche la nuit',
    'harcelement sexuel', 'mon mari me frappe', 'mon pere me frappe', 'ma mere me frappe',
    'mon frere me frappe', 'mon oncle me frappe', 'mon copain me frappe', 'mon patron me frappe', 'il me frappe', 'elle me frappe', 'ils me frappent', 'il me bat', 'ils me battent',
    'violence conjugale', 'violences conjugales', 'je suis battue', 'mariage force', 'excisee', 'excision',
]
