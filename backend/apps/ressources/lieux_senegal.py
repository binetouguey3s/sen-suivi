"""Les 98 sites de docs/Sen_Suivi_Sites_Detente_Senegal.pdf (édition novembre 2026).

Nom, localité, type de lieu, accès et précisions sont recopiés du PDF. Les
descriptions ne reprennent que ces colonnes ; les 8 lieux déjà publiés gardent
la leur (contenus_demo.LIEUX). Coordonnées : repère approximatif, à l'échelle
de la localité, et None dès que la position n'est pas sûre ou que le site est
étendu ou réparti sur plusieurs endroits.
"""

from datetime import date

from .contenus_demo import LIEUX as LIEUX_DEJA_PUBLIES
from .models import AccesLieu as A
from .models import CategorieLieu as C
from .models import Region as R

DERNIERE_VERIFICATION = date(2026, 11, 1)

# Nom du lieu dans le PDF → nom qu'il portait en base avant l'import
ANCIENS_NOMS = {
    'Parc Forestier et Zoologique de Hann': 'Parc Forestier de Hann',
    'Lac Rose (Lac Retba)': 'Lac Rose',
    'Lagune de la Somone (RNIC)': 'Lagune de la Somone',
    'Corniche Ouest & parcours sportifs': 'Corniche Ouest',
    'Île de Gorée': 'Île de Gorée',
    'Toubab Dialaw': 'Toubab Dialaw',
    'Plages publiques (Ngor, Yoff, Virage, Anse Bernard, Malibu)': 'Plage de Ngor',
    'Réserve Naturelle de Popenguine': 'Popenguine',
}

_DEJA_PUBLIE = None  # description et coordonnées viennent de contenus_demo.LIEUX

# (nom, localité, type de lieu, catégorie, accès, précisions, description, coordonnées)
_SITES = {
    R.DAKAR: [
        ('Parc Forestier et Zoologique de Hann', 'Hann Bel-Air', 'Parc arboré, zoo, jardin botanique, lac', C.PARCS, A.MIXTE,
         'Parc gratuit ; zoo payant (≈ 500 F adulte / 300 F enfant)', _DEJA_PUBLIE, None),
        ('Parc National des Îles de la Madeleine', 'Au large de Dakar', 'Parc national insulaire', C.RESERVES, A.PAYANT,
         'Permis DPN + traversée en pirogue', 'Parc national insulaire situé au large de Dakar.', (14.6547, -17.4700)),
        ('Réserve Naturelle Urbaine de la Grande Niaye de Pikine', 'Pikine', 'Zone humide urbaine, oiseaux', C.RESERVES, A.GRATUIT,
         'Officiellement gratuit', 'Réserve naturelle urbaine à Pikine : une zone humide où vivent des oiseaux.', None),
        ('Forêt classée de Mbao', 'Mbao', 'Forêt périurbaine', C.FORETS, A.LIBRE,
         'Accès libre, peu aménagé', 'Forêt périurbaine classée, située à Mbao.', None),
        ('Lac Rose (Lac Retba)', 'Niaga / Bambilor', 'Lac salé, dunes, plage', C.LACS, A.MIXTE,
         'Site libre ; pirogue, quad, cheval payants', _DEJA_PUBLIE, None),
        ('Parc exotique Le Mbossé', 'Lac Rose', 'Parc exotique / jardin', C.PARCS, A.PAYANT,
         'Entrée ou séjour payant', 'Parc exotique et jardin situé au Lac Rose.', None),
        ('Village des Tortues (Réserve botanique de Noflaye)', 'Noflaye / Sangalkam', 'Centre de protection des tortues', C.PARCS, A.PAYANT,
         'Visite payante', 'Centre de protection des tortues, à Noflaye et Sangalkam.', None),
        ('Phare des Mamelles', 'Ouakam', 'Colline, terrasse panoramique', C.PATRIMOINE, A.PAYANT,
         "Ticket d'entrée", 'Colline de Ouakam dotée d’une terrasse panoramique.', (14.7236, -17.4975)),
        ('Monument de la Renaissance Africaine', 'Ouakam', 'Colline, point de vue', C.PATRIMOINE, A.MIXTE,
         'Esplanade libre ; visite intérieure payante', 'Colline de Ouakam offrant un point de vue.', (14.7219, -17.4947)),
        ('Île de Ngor', 'Ngor', 'Île, plages, surf', C.ILES, A.PAYANT,
         'Pirogue payante', 'Île de Ngor, avec ses plages et un spot de surf.', (14.7560, -17.5140)),
        ('Île de Gorée', 'Gorée', 'Île patrimoniale (UNESCO), plage', C.ILES, A.PAYANT,
         'Chaloupe + taxe touristique', _DEJA_PUBLIE, None),
        ('Pointe des Almadies', 'Almadies', 'Littoral rocheux, point extrême ouest', C.PLAGES, A.LIBRE,
         'Accès libre', 'Littoral rocheux des Almadies, au point extrême ouest.', (14.7436, -17.5306)),
        ('Corniche Ouest & parcours sportifs', 'Fann – Ouakam', 'Promenade, sport en plein air', C.PLAGES, A.GRATUIT,
         'Gratuit', _DEJA_PUBLIE, None),
        ('Plages publiques (Ngor, Yoff, Virage, Anse Bernard, Malibu)', 'Dakar', 'Plages', C.PLAGES, A.GRATUIT,
         'Gratuit (transats/clubs payants)', _DEJA_PUBLIE, None),
        ('Toubab Dialaw', 'Yène', "Falaises, plage, village d'artistes", C.PLAGES, A.LIBRE,
         'Accès libre', _DEJA_PUBLIE, None),
        ('Place des Cultures Urbaines (skatepark)', "Patte d'Oie", 'Espace de loisirs urbain', C.PARCS, A.GRATUIT,
         'Gratuit', "Espace de loisirs urbain avec skatepark, à Patte d'Oie.", None),
    ],
    R.THIES: [
        ('Réserve Naturelle de Popenguine', 'Popenguine', 'Réserve, sentiers, falaise, plage', C.RESERVES, A.MIXTE,
         'Sentiers payants ; plage gratuite', _DEJA_PUBLIE, None),
        ('Réserve de Bandia', 'Sindia / Mbour', 'Réserve animalière, safari', C.RESERVES, A.PAYANT,
         'Entrée + visite guidée', 'Réserve animalière entre Sindia et Mbour, qui se découvre en safari.', (14.5833, -17.0167)),
        ('Parc Exotique du Sénégal (reptiles)', 'Nguérigne Bambara', 'Parc animalier et de loisirs', C.PARCS, A.PAYANT,
         'Payant', 'Parc animalier et de loisirs consacré aux reptiles, à Nguérigne Bambara.', None),
        ('Lagune de la Somone (RNIC)', 'Somone', 'Lagune, mangrove, oiseaux', C.LACS, A.MIXTE,
         'Promenade gratuite ; pirogue payante', _DEJA_PUBLIE, None),
        ('Accrobaobab', 'Sindia', 'Parc aventure dans les baobabs', C.PARCS, A.PAYANT,
         'Payant', 'Parc aventure installé dans les baobabs, à Sindia.', None),
        ('Lac Tanma', 'Keur Moussa / Tivaouane', "Lac, oiseaux d'eau", C.LACS, A.LIBRE,
         'Accès libre', "Lac fréquenté par les oiseaux d'eau, entre Keur Moussa et Tivaouane.", None),
        ('AMP de Joal-Fadiouth – Île aux coquillages', 'Joal-Fadiouth', 'Aire marine, île, mangrove', C.ILES, A.PAYANT,
         "Visite guidée de l'île payante", 'Aire marine protégée de Joal-Fadiouth, entre île et mangrove.', (14.1550, -16.8270)),
        ('AMP de Kayar', 'Kayar', 'Aire marine, plage de pêche', C.PLAGES, A.LIBRE,
         'Accès libre', 'Aire marine protégée de Kayar, avec sa plage de pêche.', (14.9167, -17.1167)),
        ('Plages de Saly, Ngaparou, Mbour', 'Petite Côte', 'Plages balnéaires', C.PLAGES, A.GRATUIT,
         'Plages publiques gratuites', 'Plages balnéaires de la Petite Côte, à Saly, Ngaparou et Mbour.', None),
        ('Plage de Ndayane / Popenguine', 'Popenguine-Ndayane', 'Plage, falaises', C.PLAGES, A.GRATUIT,
         'Gratuit', 'Plage bordée de falaises, à Popenguine-Ndayane.', None),
        ('Réserve écologique expérimentale de Mbour', 'Mbour', 'Réserve scientifique', C.RESERVES, A.RESTREINT,
         'Sur autorisation', 'Réserve scientifique située à Mbour.', None),
    ],
    R.SAINT_LOUIS: [
        ('Parc National des Oiseaux du Djoudj', 'Ross Béthio (Dagana)', 'Sanctuaire ornithologique (UNESCO)', C.RESERVES, A.PAYANT,
         'Permis DPN + pirogue ; saison nov.–avril', 'Sanctuaire ornithologique inscrit à l’UNESCO, à Ross Béthio.', (16.3667, -16.2667)),
        ('Parc National de la Langue de Barbarie', 'Gandiol', 'Embouchure, dunes, oiseaux, tortues', C.RESERVES, A.PAYANT,
         'Permis DPN + pirogue', 'Parc national de Gandiol, entre embouchure et dunes, où vivent oiseaux et tortues.', (15.8800, -16.5100)),
        ('Réserve Spéciale de Faune de Guembeul', 'Guembeul', 'Gazelles, tortues, lagune', C.RESERVES, A.PAYANT,
         'Permis DPN', 'Réserve de faune de Guembeul : une lagune, des gazelles et des tortues.', (15.9167, -16.4667)),
        ("Réserve Spéciale d'Avifaune du Ndiaël", 'Ross Béthio', 'Zone humide, oiseaux', C.RESERVES, A.PAYANT,
         'Permis DPN', "Réserve d'avifaune à Ross Béthio : une zone humide où vivent des oiseaux.", None),
        ('RNC de Tocc Tocc (Lac de Guiers)', 'Ronkh / Richard-Toll', 'Réserve communautaire, lamantins, tortues', C.RESERVES, A.PAYANT,
         'Contribution communautaire', 'Réserve communautaire sur le lac de Guiers, où vivent lamantins et tortues.', None),
        ('Lac de Guiers', 'Richard-Toll / Keur Momar Sarr', "Grand lac d'eau douce", C.LACS, A.LIBRE,
         'Accès libre', "Grand lac d'eau douce, entre Richard-Toll et Keur Momar Sarr.", (16.2000, -15.8500)),
        ('AMP de Saint-Louis', 'Saint-Louis', 'Aire marine protégée', C.PLAGES, A.LIBRE,
         'Accès libre', 'Aire marine protégée de Saint-Louis.', None),
        ("Réserve animalière d'Amboura", "Podor (forêt d'Amboura)", 'Réserve animalière (PPP)', C.RESERVES, A.PAYANT,
         'Payant', "Réserve animalière située dans la forêt d'Amboura, à Podor.", None),
        ('Île de Saint-Louis & Hydrobase', 'Saint-Louis', 'Ville UNESCO, plage', C.ILES, A.GRATUIT,
         'Gratuit', 'Ville inscrite à l’UNESCO et plage, à Saint-Louis.', (16.0270, -16.5040)),
        ('Berges du fleuve – Île à Morphil', 'Podor', 'Fleuve, paysages sahéliens', C.FLEUVES, A.LIBRE,
         'Accès libre ; bac payant', 'Berges du fleuve à Podor, dans des paysages sahéliens.', (16.6533, -14.9583)),
    ],
    R.LOUGA: [
        ('Désert de Lompoul', 'Lompoul (Kébémer)', 'Dunes, désert', C.DESERT, A.MIXTE,
         'Désert libre ; campements payants', 'Désert et dunes de Lompoul, dans le Kébémer.', (15.4500, -16.7000)),
        ('Lompoul-sur-Mer / Grande Côte', 'Kébémer', 'Plage sauvage, Niayes', C.PLAGES, A.LIBRE,
         'Accès libre', 'Plage sauvage de la Grande Côte, dans les Niayes.', None),
        ('Plage de Potou', 'Potou', 'Plage, Niayes maraîchères', C.PLAGES, A.LIBRE,
         'Accès libre', 'Plage de Potou et Niayes maraîchères.', None),
        ('Lac de Guiers (rive ouest)', 'Keur Momar Sarr', "Lac d'eau douce", C.LACS, A.LIBRE,
         'Accès libre', "Rive ouest du lac d'eau douce de Guiers, à Keur Momar Sarr.", (15.9167, -15.9667)),
        ('Réserves sylvo-pastorales de Barkédji-Dodji', 'Linguère', 'Savane sahélienne, pastoralisme', C.RESERVES, A.LIBRE,
         'Accès libre (guide conseillé)', 'Savane sahélienne et terres de pastoralisme, à Linguère.', None),
        ('Réserve de faune du Ferlo Nord (partie ouest)', 'Linguère', 'Steppe sahélienne', C.RESERVES, A.PAYANT,
         'Permis DPN', 'Partie ouest de la réserve du Ferlo Nord : une steppe sahélienne, à Linguère.', None),
    ],
    R.MATAM: [
        ('Réserve de faune du Ferlo Nord', 'Ranérou / Ourossogui', 'Steppe, autruches, gazelles, tortues sulcata', C.RESERVES, A.PAYANT,
         'Permis DPN ; saison déc.–juin', 'Steppe où vivent autruches, gazelles et tortues sulcata, entre Ranérou et Ourossogui.', None),
        ('Réserve de faune du Ferlo Sud', 'Ranérou', 'Savane sahélienne', C.RESERVES, A.PAYANT,
         'Permis DPN', 'Réserve de faune en savane sahélienne, à Ranérou.', None),
        ('Forêt classée de Diamel', 'Ranérou', 'Forêt classée', C.FORETS, A.LIBRE,
         'Accès libre', 'Forêt classée située à Ranérou.', None),
        ('Forêt-galerie de Matam', 'Matam', 'Forêt riveraine', C.FORETS, A.LIBRE,
         'Accès libre', 'Forêt riveraine située à Matam.', None),
        ('Berges du fleuve Sénégal', 'Matam / Ourossogui', 'Fleuve, pirogue, paysages', C.FLEUVES, A.LIBRE,
         'Accès libre ; pirogue payante', 'Berges du fleuve Sénégal, entre Matam et Ourossogui, à parcourir aussi en pirogue.', None),
    ],
    R.TAMBACOUNDA: [
        ('Parc National du Niokolo-Koba', 'Tambacounda / Kédougou / Kolda', 'Grand parc national, savane (UNESCO)', C.RESERVES, A.PAYANT,
         'Permis DPN + guide/véhicule', 'Grand parc national de savane inscrit à l’UNESCO, entre Tambacounda, Kédougou et Kolda.', (13.0667, -13.1667)),
        ('Réserve Naturelle Communautaire du Boundou', 'Goudiry (entrée Koussan)', 'Steppe, forêts, gazelles', C.RESERVES, A.PAYANT,
         'Écoguides payants', 'Réserve communautaire de steppe et de forêts où vivent des gazelles, avec une entrée à Koussan.', None),
        ('Réserve de faune du Ferlo Sud (partie sud)', 'Nord de Tambacounda', 'Savane sahélienne', C.RESERVES, A.PAYANT,
         'Permis DPN', 'Partie sud de la réserve du Ferlo Sud : une savane sahélienne, au nord de Tambacounda.', None),
        ('Wassadou – fleuve Gambie', 'Wassadou', 'Fleuve, hippopotames, oiseaux', C.FLEUVES, A.PAYANT,
         'Campement / pirogue', 'Fleuve Gambie à Wassadou, où vivent hippopotames et oiseaux.', (13.3500, -13.3700)),
        ('Berges du Sénégal & Falémé', 'Bakel', 'Fleuve, collines', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Berges de fleuve et collines, à Bakel.', (14.9000, -12.4667)),
    ],
    R.KEDOUGOU: [
        ('Cascade et RNC de Dindéfélo', 'Dindéfélo', 'Cascade ~100 m, forêt, chimpanzés', C.CASCADES, A.PAYANT,
         'Contribution communautaire', "Cascade d'environ 100 m à Dindéfélo, dans une forêt où vivent des chimpanzés.", (12.3667, -12.3333)),
        ('Cascade de Ségou', 'Ségou (Dindéfélo)', 'Cascade, canyon', C.CASCADES, A.PAYANT,
         'Guide local', 'Cascade et canyon de Ségou, dans le secteur de Dindéfélo.', None),
        ('Cascades de Fongolimbi (Kafory, Kounsi, Lombel)', 'Fongolimbi', 'Cascades, forêt', C.CASCADES, A.PAYANT,
         'Guide local', 'Cascades et forêt de Fongolimbi.', None),
        ('Mont Assirik', 'Niokolo-Koba', 'Point culminant, panorama', C.CASCADES, A.PAYANT,
         'Permis DPN', 'Point culminant offrant un panorama, à Niokolo-Koba.', (12.8833, -12.7667)),
        ('Pays Bassari & Iwol (Bandafassi)', 'Bandafassi', 'Villages perchés (UNESCO), randonnée', C.PATRIMOINE, A.PAYANT,
         'Contribution villageoise', 'Villages perchés inscrits à l’UNESCO, à découvrir en randonnée depuis Bandafassi.', (12.5333, -12.3000)),
        ('Grottes de Dandé', 'Dandé', 'Grottes, montagne', C.CASCADES, A.PAYANT,
         'Guide local', 'Grottes de montagne situées à Dandé.', None),
        ('Fleuve Gambie à Kédougou / Mako', 'Kédougou, Mako', 'Fleuve, baignade, pirogue', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Fleuve Gambie à Kédougou et Mako, pour la baignade et la pirogue.', (12.5567, -12.1747)),
    ],
    R.KOLDA: [
        ('Forêts classées (Koudoura, Mampaye, Mahon, Pata)', 'Kolda / Vélingara', 'Forêts, savane boisée', C.FORETS, A.LIBRE,
         'Accès libre', 'Forêts classées et savane boisée, entre Kolda et Vélingara.', None),
        ('Berges du fleuve Casamance', 'Kolda', 'Fleuve, promenade', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Promenade le long du fleuve Casamance, à Kolda.', (12.8833, -14.9500)),
        ('Parc du Niokolo-Koba (frange sud)', 'Vélingara', 'Parc national', C.RESERVES, A.PAYANT,
         'Permis DPN', 'Frange sud du parc national du Niokolo-Koba, à Vélingara.', None),
        ('Tata de Moussa Molo Baldé', 'Ndorna (Médina Yoro Foulah)', 'Site historique', C.PATRIMOINE, A.LIBRE,
         'Accès libre', 'Site historique situé à Ndorna, dans le Médina Yoro Foulah.', None),
    ],
    R.SEDHIOU: [
        ('Fleuve Casamance & bac de Sédhiou', 'Sédhiou', 'Fleuve, bolongs, pirogue', C.FLEUVES, A.MIXTE,
         'Berges libres ; bac payant', 'Fleuve Casamance et bolongs à Sédhiou, à parcourir aussi en pirogue.', (12.7083, -15.5569)),
        ('Forêt de Sefa', 'Près de Sédhiou', 'Forêt riveraine', C.FORETS, A.LIBRE,
         'Accès libre', 'Forêt riveraine située près de Sédhiou.', None),
        ('Bolongs du Soungrougrou', 'Marsassoum', 'Mangrove, oiseaux', C.FLEUVES, A.LIBRE,
         'Accès libre ; pirogue payante', 'Mangrove de Marsassoum, où vivent des oiseaux.', (12.8283, -15.9806)),
        ('Fort de Sédhiou', 'Sédhiou', 'Site historique en bord de fleuve', C.PATRIMOINE, A.LIBRE,
         'Accès libre', 'Site historique en bord de fleuve, à Sédhiou.', (12.7083, -15.5569)),
    ],
    R.ZIGUINCHOR: [
        ('Parc National de Basse Casamance', 'Oussouye', 'Forêt dense, mangrove', C.RESERVES, A.RESTREINT,
         'Actuellement non visitable', 'Parc national de forêt dense et de mangrove, à Oussouye.', (12.4000, -16.5833)),
        ('Réserve Ornithologique de Kalissaye', 'Kafountine', "Îlots, colonies d'oiseaux", C.RESERVES, A.RESTREINT,
         'Accès restreint, à vérifier', "Îlots abritant des colonies d'oiseaux, à Kafountine.", None),
        ("AMP d'Abéné", 'Abéné', 'Aire marine, plage', C.PLAGES, A.LIBRE,
         'Accès libre', "Aire marine protégée et plage d'Abéné.", (13.0533, -16.7250)),
        ('AMP de Niamone-Kalounayes', 'Bignona', 'Mangrove, bolongs', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Aire marine protégée de mangrove et de bolongs, à Bignona.', None),
        ('AMP de Kassa-Balantacounda', 'Basse-Casamance', 'Mangrove, estuaire', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Aire marine protégée de mangrove et d’estuaire, en Basse-Casamance.', None),
        ('Île de Carabane', 'Embouchure de la Casamance', 'Île, plage, patrimoine', C.ILES, A.PAYANT,
         'Pirogue payante', 'Île à l’embouchure de la Casamance, entre plage et patrimoine.', (12.5333, -16.7000)),
        ('Plages de Cap Skirring & Kabrousse', 'Oussouye', 'Plages', C.PLAGES, A.GRATUIT,
         'Gratuit', 'Plages de Cap Skirring et de Kabrousse, dans le secteur d’Oussouye.', (12.3950, -16.7467)),
        ('Diembering & forêt de Bouyouye', 'Diembering', 'Plage, fromagers géants', C.PLAGES, A.LIBRE,
         'Accès libre', 'Plage de Diembering et fromagers géants.', (12.4667, -16.7833)),
        ('Plages de Kafountine & Abéné', 'Bignona', 'Plages, pêche', C.PLAGES, A.GRATUIT,
         'Gratuit', 'Plages et pêche à Kafountine et Abéné, dans le secteur de Bignona.', None),
        ('Îles et bolongs (Elinkine, Pointe St-Georges, Niomoune)', 'Basse-Casamance', 'Mangrove, îles', C.ILES, A.PAYANT,
         'Pirogue payante', 'Îles et mangrove de Basse-Casamance : Elinkine, Pointe St-Georges et Niomoune.', None),
    ],
    R.FATICK: [
        ('Parc National du Delta du Saloum', 'Foundiougne / Palmarin', 'Mangrove, écosystème marin (UNESCO)', C.RESERVES, A.PAYANT,
         'Permis DPN + pirogue', 'Mangrove et écosystème marin inscrits à l’UNESCO, entre Foundiougne et Palmarin.', (13.6167, -16.6333)),
        ('Réserve de Fathala', 'Karang / Toubacouta', 'Réserve animalière, marche avec lions', C.RESERVES, A.PAYANT,
         'Payant (excursions depuis Dakar ~65 000 F)', 'Réserve animalière entre Karang et Toubacouta, qui propose la marche avec les lions.', (13.6500, -16.4500)),
        ('RNC de Palmarin', 'Palmarin', 'Lagunes, tortues, oiseaux', C.LACS, A.MIXTE,
         'Plage libre ; activités guidées payantes', 'Réserve communautaire de Palmarin : des lagunes, des tortues et des oiseaux.', (14.0000, -16.7500)),
        ('AMP du Bamboung', 'Toubacouta / Sipo', 'Bolong, mangrove', C.FLEUVES, A.PAYANT,
         'Campement / pirogue', 'Aire marine protégée de bolong et de mangrove, entre Toubacouta et Sipo.', None),
        ('AMP de Sangomar & Pointe de Sangomar', 'Palmarin / Dionewar', 'Flèche sableuse, îles', C.ILES, A.PAYANT,
         'Pirogue payante', 'Flèche sableuse et îles, entre Palmarin et Dionewar.', (13.8333, -16.7667)),
        ('AMP de Gandoul', 'Djirnda', 'Îles, mangrove', C.ILES, A.PAYANT,
         'Pirogue payante', 'Îles et mangrove de l’aire marine protégée de Gandoul, à Djirnda.', None),
        ('Îles du Saloum (Mar Lodj, Dionewar, Niodior)', 'Delta du Saloum', 'Îles, mangrove', C.ILES, A.PAYANT,
         'Pirogue payante', 'Îles et mangrove du delta du Saloum : Mar Lodj, Dionewar et Niodior.', None),
        ('Bolongs de Toubacouta / Sokone', 'Toubacouta', 'Mangrove, oiseaux', C.FLEUVES, A.PAYANT,
         'Pirogue payante', 'Mangrove de Toubacouta, où vivent des oiseaux.', (13.7833, -16.4750)),
        ('Ndangane & Djiffer', 'Fimela', 'Bord de mer, départ en pirogue', C.PLAGES, A.LIBRE,
         'Accès libre', 'Bord de mer de Fimela, point de départ en pirogue.', None),
    ],
    R.KAOLACK: [
        ('Sites mégalithiques de Sine Ngayène', 'Nioro du Rip', 'Cercles de pierres (UNESCO)', C.PATRIMOINE, A.PAYANT,
         'Droit de visite modique (à vérifier)', 'Cercles de pierres inscrits à l’UNESCO, à Nioro du Rip.', (13.6891, -15.5333)),
        ('Salins du Sine-Saloum / tannes', 'Kaolack', 'Paysages de sel', C.LACS, A.LIBRE,
         'Vue libre ; visite guidée sur demande', 'Paysages de sel à Kaolack.', None),
        ('Berges du Saloum', 'Kaolack', 'Fleuve, promenade', C.FLEUVES, A.LIBRE,
         'Accès libre', 'Promenade le long du fleuve, à Kaolack.', None),
        ('Grande Mosquée de Médina Baye', 'Médina Baye', 'Site religieux, patrimoine', C.PATRIMOINE, A.LIBRE,
         'Libre (tenue correcte)', 'Site religieux et patrimonial de Médina Baye.', (14.1560, -16.0850)),
        ('Village artisanal de Kaolack', 'Kaolack', 'Artisanat', C.PATRIMOINE, A.LIBRE,
         'Accès libre', "Lieu consacré à l'artisanat, à Kaolack.", None),
    ],
    R.KAFFRINE: [
        ('Cercles mégalithiques de Wanar', 'Wanar (Kaffrine)', 'Cercles de pierres (UNESCO)', C.PATRIMOINE, A.PAYANT,
         'Droit de visite modique (à vérifier)', 'Cercles de pierres inscrits à l’UNESCO, à Wanar.', (13.7575, -15.5150)),
        ('Zones humides saisonnières', 'Autour de Kaffrine', "Mares, oiseaux d'eau (hivernage)", C.LACS, A.LIBRE,
         'Accès libre', "Mares autour de Kaffrine, où vivent des oiseaux d'eau pendant l'hivernage.", None),
        ('Savane à baobabs & collines', 'Kaffrine', 'Paysages ruraux, levers de soleil', C.FORETS, A.LIBRE,
         'Accès libre', 'Paysages ruraux de Kaffrine, à contempler au lever du soleil.', None),
    ],
    R.DIOURBEL: [
        ('Grande Mosquée de Touba', 'Touba', 'Site religieux, esplanade', C.PATRIMOINE, A.LIBRE,
         'Libre (tenue correcte)', 'Site religieux et esplanade, à Touba.', (14.8600, -15.8750)),
        ('Fonderie Makhone Diop', 'Diourbel', 'Artisanat, patrimoine', C.PATRIMOINE, A.LIBRE,
         'Visite libre', "Lieu d'artisanat et de patrimoine, à Diourbel.", None),
        ('Ville de Diourbel & mosquée', 'Diourbel', 'Patrimoine religieux', C.PATRIMOINE, A.LIBRE,
         'Accès libre', 'Patrimoine religieux de la ville de Diourbel.', (14.6550, -16.2314)),
    ],
}

# Points de vigilance : page 10 du PDF
_SAISON_SECHE = (
    "Visites surtout en saison sèche (environ novembre/décembre à avril/juin). "
    "Pistes souvent impraticables pendant l'hivernage."
)
_NON_VISITABLE = (
    'Signalé comme non visitable ou fermé : vérifiez auprès de la Direction des Parcs Nationaux (DPN) '
    'avant de vous déplacer.'
)
_TARIFS_PRIVES = 'Les tarifs de ce site changent souvent : vérifiez-les avant de venir.'

VIGILANCE = {
    'Parc National de Basse Casamance': _NON_VISITABLE,
    'Réserve Ornithologique de Kalissaye': _NON_VISITABLE,
    'Cascade et RNC de Dindéfélo': (
        "Feux de brousse importants signalés en mars 2026. Contactez le centre d'accueil avant tout déplacement "
        '(zone proche de la frontière guinéenne).'
    ),
    'Parc National des Oiseaux du Djoudj': _SAISON_SECHE,
    'Réserve de faune du Ferlo Nord (partie ouest)': _SAISON_SECHE,
    'Réserve de faune du Ferlo Nord': _SAISON_SECHE,
    'Réserve de faune du Ferlo Sud': _SAISON_SECHE,
    'Réserve de faune du Ferlo Sud (partie sud)': _SAISON_SECHE,
    'Parc National du Niokolo-Koba': _SAISON_SECHE,
    'Parc du Niokolo-Koba (frange sud)': _SAISON_SECHE,
    'Mont Assirik': _SAISON_SECHE,
    'Réserve de Bandia': _TARIFS_PRIVES,
    'Réserve de Fathala': _TARIFS_PRIVES,
    'Accrobaobab': _TARIFS_PRIVES,
    'Parc Exotique du Sénégal (reptiles)': _TARIFS_PRIVES,
    'Parc exotique Le Mbossé': _TARIFS_PRIVES,
}

MEILLEURE_PERIODE = {
    'Parc National des Oiseaux du Djoudj': 'Novembre à avril',
    'Réserve de faune du Ferlo Nord': 'Décembre à juin',
    'Réserve de faune du Ferlo Nord (partie ouest)': 'Saison sèche',
    'Réserve de faune du Ferlo Sud': 'Saison sèche',
    'Réserve de faune du Ferlo Sud (partie sud)': 'Saison sèche',
    'Parc National du Niokolo-Koba': 'Saison sèche',
    'Parc du Niokolo-Koba (frange sud)': 'Saison sèche',
    'Mont Assirik': 'Saison sèche',
}


def _site(region, nom, ville, type_lieu, categorie, acces, precisions, description, coordonnees):
    if description is _DEJA_PUBLIE:
        publie = LIEUX_DEJA_PUBLIES[nom]
        description, coordonnees = publie['description'], (publie['latitude'], publie['longitude'])
    latitude, longitude = coordonnees or (None, None)
    return {
        'nom': nom,
        'region': region.value,
        'ville': ville,
        'type_lieu': type_lieu,
        'categorie': categorie.value,
        'acces': acces.value,
        'precisions': precisions,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'vigilance': VIGILANCE.get(nom, ''),
        'meilleure_periode': MEILLEURE_PERIODE.get(nom, ''),
        'derniere_verification': DERNIERE_VERIFICATION,
    }


LIEUX_SENEGAL = [_site(region, *site) for region, sites in _SITES.items() for site in sites]
