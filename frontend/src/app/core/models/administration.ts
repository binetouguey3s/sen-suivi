// Types correspondant aux sérialiseurs Django (écrans d'administration).

export interface VueEnsembleAdmin {
  professionnels_en_attente: number;
  publications_en_attente: number;
  commentaires_en_attente: number;
}

export type StatutValidationPro = 'EN_ATTENTE' | 'VALIDE' | 'REFUSE';

export interface ProfessionnelAdmin {
  id: number;
  nom: string;
  email: string;
  specialite: string;
  specialite_affichee: string;
  ville: string;
  langue: string;
  tarif_indicatif: number;
  presentation: string;
  statut_validation: StatutValidationPro;
  statut_validation_affiche: string;
  date_creation: string;
}

export type StatutModerationForum = 'EN_ATTENTE' | 'VISIBLE' | 'MASQUE' | 'SUPPRIME';

export interface PublicationForumAdmin {
  id: number;
  pseudonyme: string;
  titre: string;
  contenu: string;
  thematique: string;
  thematique_affichee: string;
  date: string;
  statut_moderation: StatutModerationForum;
}

export interface CommentaireForumAdmin {
  id: number;
  pseudonyme: string;
  publication: number;
  publication_titre: string;
  contenu: string;
  date: string;
  statut_moderation: StatutModerationForum;
}

export interface RessourceAdmin {
  id: number;
  titre: string;
  type_ressource: 'ARTICLE' | 'EXERCICE' | 'PODCAST';
  contenu: string;
  thematique: string;
  duree_lecture: number;
  date_publication: string;
}
