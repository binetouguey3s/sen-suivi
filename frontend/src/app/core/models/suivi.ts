// Types correspondant aux sérialiseurs Django (apps/suivi, apps/ressources).
// Noms de champs en snake_case : ce sont exactement ceux renvoyés par l'API.

export type NiveauHumeur = 'TRES_MAL' | 'MAL' | 'NEUTRE' | 'BIEN' | 'TRES_BIEN';

export const NIVEAUX_HUMEUR: { valeur: NiveauHumeur; emoji: string; libelle: string; score: number }[] = [
  { valeur: 'TRES_MAL', emoji: '😫', libelle: 'Très mal', score: 1 },
  { valeur: 'MAL', emoji: '🙁', libelle: 'Mal', score: 2 },
  { valeur: 'NEUTRE', emoji: '😐', libelle: 'Neutre', score: 3 },
  { valeur: 'BIEN', emoji: '🙂', libelle: 'Bien', score: 4 },
  { valeur: 'TRES_BIEN', emoji: '😊', libelle: 'Très bien', score: 5 },
];

export interface SuiviHumeur {
  id: number;
  date: string;
  score_humeur: NiveauHumeur;
  note: string;
  etiquettes: string;
}

// Facteurs d'influence proposés dans la maquette Journal d'humeur : pas de
// modèle dédié côté back-end, stockés comme une simple chaîne (etiquettes).
export const INFLUENCES_HUMEUR = [
  'Travail',
  'Famille',
  'Études',
  'Sommeil',
  'Santé',
  'Argent',
  'Transport',
] as const;

export interface Ressource {
  id: number;
  titre: string;
  type_ressource: 'ARTICLE' | 'EXERCICE' | 'PODCAST';
  contenu: string;
  thematique: string;
}

export interface LieuDetente {
  id: number;
  nom: string;
  ville: string;
  description: string;
  categorie: string;
}
