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

export type TypeRessource = 'ARTICLE' | 'EXERCICE' | 'PODCAST' | 'VIDEO';
export type StatutRessource = 'BROUILLON' | 'EN_ATTENTE' | 'PUBLIEE' | 'REFUSEE';

// Crédit d'une ressource proposée par un professionnel
export interface AuteurRessource {
  id: number;
  nom: string;
  specialite_affichee: string;
}

export interface Ressource {
  id: number;
  titre: string;
  type_ressource: TypeRessource;
  contenu: string;
  thematique: string;
  duree_lecture: number;
  date_publication: string;
  // Podcast : « /audio/podcasts/… » ou adresse https ; vide si aucun fichier
  url_audio?: string;
  // À lire : le fichier envoyé depuis le formulaire en priorité, sinon url_audio
  audio?: string;
  // Vidéo : seul l'identifiant YouTube sert à l'intégration
  url_video?: string;
  video_id?: string | null;
  // null : créée par l'administration
  auteur?: AuteurRessource | null;
  statut?: StatutRessource;
  motif_refus?: string;
  date_soumission?: string | null;
  date_modification?: string;
}

export interface LieuDetente {
  id: number;
  nom: string;
  ville: string;
  description: string;
  categorie: string;
  latitude: number | null;
  longitude: number | null;
  acces_libre: boolean;
}
