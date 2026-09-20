// Types correspondant aux sérialiseurs Django (apps/forum).

export type ThematiqueForum = 'STRESS' | 'SOMMEIL' | 'RELATIONS' | 'TRAVAIL' | 'DEUIL';

export const THEMATIQUES_FORUM: { valeur: ThematiqueForum; libelle: string }[] = [
  { valeur: 'STRESS', libelle: 'Stress' },
  { valeur: 'SOMMEIL', libelle: 'Sommeil' },
  { valeur: 'RELATIONS', libelle: 'Relations' },
  { valeur: 'TRAVAIL', libelle: 'Travail' },
  { valeur: 'DEUIL', libelle: 'Deuil' },
];

export interface PublicationForum {
  id: number;
  pseudonyme: string;
  titre: string;
  contenu: string;
  thematique: ThematiqueForum;
  date: string;
  nb_reponses: number;
}

export interface CommentaireForum {
  id: number;
  pseudonyme: string;
  contenu: string;
  date: string;
}

export interface SujetSimilaire {
  id: number;
  titre: string;
  nb_reponses: number;
}

export interface PublicationForumDetail extends PublicationForum {
  commentaires: CommentaireForum[];
  sujets_similaires: SujetSimilaire[];
}
