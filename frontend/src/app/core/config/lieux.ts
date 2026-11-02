import { NomIcone } from '../icons/icons';
import { AccesLieu } from '../models/suivi';

export const REGIONS = [
  'Dakar', 'Thiès', 'Saint-Louis', 'Louga', 'Matam', 'Tambacounda', 'Kédougou',
  'Kolda', 'Sédhiou', 'Ziguinchor', 'Fatick', 'Kaolack', 'Kaffrine', 'Diourbel',
] as const;

export type FamilleCouverture = 'eau' | 'vert' | 'sable';

export interface CategorieLieu {
  nom: string;
  icone: NomIcone;
  famille: FamilleCouverture;
  // Conseil de bien-être générique, jamais un fait sur le lieu
  bienEtre: string;
  // Thématique existante de la bibliothèque de ressources
  thematique: string;
}

export const CATEGORIES: CategorieLieu[] = [
  {
    nom: 'Plages & littoral', icone: 'vagues', famille: 'eau', thematique: 'Respiration',
    bienEtre: 'Marcher pieds nus en écoutant les vagues aide à relâcher la tension. Calez votre souffle sur le va-et-vient de l’eau, quelques minutes suffisent.',
  },
  {
    nom: 'Parcs & jardins', icone: 'feuille', famille: 'vert', thematique: 'Stress',
    bienEtre: 'Ralentissez le pas et posez votre attention sur ce qui vous entoure : une couleur, une odeur, un chant d’oiseau. Ce petit exercice aide à sortir des pensées qui tournent en boucle.',
  },
  {
    nom: 'Parcs nationaux & réserves', icone: 'oiseau', famille: 'vert', thematique: 'Bien-être',
    bienEtre: 'Prenez le temps d’observer sans chercher à tout voir. Rester quelques instants silencieux dans la nature invite le corps et l’esprit à se poser.',
  },
  {
    nom: 'Lacs & lagunes', icone: 'eau', famille: 'eau', thematique: 'Respiration',
    bienEtre: 'Asseyez-vous face à l’eau et regardez-la quelques minutes. Laissez votre respiration s’allonger, sans la forcer.',
  },
  {
    nom: 'Îles', icone: 'nature', famille: 'eau', thematique: 'Bien-être',
    bienEtre: 'La traversée peut devenir une pause : laissez le téléphone de côté et profitez de ce moment où il n’y a rien d’autre à faire que d’arriver.',
  },
  {
    nom: 'Forêts', icone: 'arbres', famille: 'vert', thematique: 'Stress',
    bienEtre: 'Marchez sans objectif de distance et sentez le sol sous vos pieds. Un rythme lent aide à faire redescendre la pression de la journée.',
  },
  {
    nom: 'Cascades & montagnes', icone: 'montagne', famille: 'vert', thematique: 'Respiration',
    bienEtre: 'Faites des pauses en chemin, respirez profondément et regardez le paysage. Avancer à votre rythme compte plus que d’arriver en haut.',
  },
  {
    nom: 'Fleuves & mangroves', icone: 'voilier', famille: 'eau', thematique: 'Sommeil',
    bienEtre: 'Suivez le courant du regard et laissez vos pensées passer comme lui, sans les retenir. Ce moment de lenteur peut aider à mieux lâcher prise le soir venu.',
  },
  {
    nom: 'Désert & dunes', icone: 'soleil', famille: 'sable', thematique: 'Sommeil',
    bienEtre: 'Écoutez le silence et levez les yeux vers l’horizon, ou vers le ciel à la nuit tombée. Ces grands espaces invitent à relativiser et à apaiser l’esprit.',
  },
  {
    nom: 'Patrimoine & culture', icone: 'monument', famille: 'sable', thematique: 'Émotions',
    bienEtre: 'Visitez sans vous presser et notez ce que ce lieu éveille en vous. Mettre des mots sur ce que l’on ressent fait souvent du bien.',
  },
];

export const CATEGORIE_PAR_NOM = new Map(CATEGORIES.map((c) => [c.nom, c]));

export const ACCES: { code: AccesLieu; libelle: string; legende: string; icone: NomIcone }[] = [
  { code: 'GRATUIT', libelle: 'Gratuit', legende: 'Entrée gratuite, site aménagé', icone: 'verifie' },
  { code: 'LIBRE', libelle: 'Accès libre', legende: 'Site naturel non clôturé (activités parfois payantes)', icone: 'feuille' },
  { code: 'PAYANT', libelle: 'Payant', legende: 'Droit d’entrée, permis, guide ou transport obligatoire', icone: 'ticket' },
  { code: 'MIXTE', libelle: 'Mixte', legende: 'Une partie gratuite, une partie payante', icone: 'billet' },
  { code: 'RESTREINT', libelle: 'Restreint', legende: 'Fermé, sur autorisation, ou accès à vérifier', icone: 'cadenas' },
];

export const ACCES_PAR_CODE = new Map(ACCES.map((a) => [a.code, a]));

export const MENTION_TARIFS = 'Tarifs indicatifs, à confirmer auprès des gestionnaires.';

// Décret 2015-1194 : s'affiche sur les lieux dont les précisions citent le permis
export const NOTE_DPN =
  'Permis d’une journée dans les parcs nationaux : 3 000 FCFA pour les nationaux, 5 000 FCFA pour les étrangers (décret 2015-1194).';
