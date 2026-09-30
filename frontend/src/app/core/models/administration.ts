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

export type StatutModerationForum = 'EN_ATTENTE' | 'VISIBLE' | 'MASQUE' | 'SUPPRIME' | 'BLOQUE';

// Ce que la modération automatique a décidé, et pourquoi
export interface DecisionIA {
  id: number;
  decision: string;
  decision_affichee: string;
  categorie: string;
  gravite: number;
  raison: string;
  extrait: string;
  niveau: 'REGLES' | 'MODELE' | 'REPLI';
  date: string;
  decision_humaine: '' | 'PUBLIER' | 'BLOQUER' | 'CLASSER';
  motif_contestation: string;
  date_contestation: string | null;
}

// File des administrateurs : doutes, détresse, blocages graves, contestations
export interface ElementFileModeration {
  id: number;
  type: 'PUBLICATION' | 'COMMENTAIRE';
  objet_id: number;
  pseudonyme: string;
  titre: string;
  contenu: string;
  statut_moderation: StatutModerationForum;
  decision: string;
  decision_affichee: string;
  categorie: string;
  gravite: number;
  raison: string;
  extrait: string;
  niveau: 'REGLES' | 'MODELE' | 'REPLI';
  priorite: number;
  date: string;
  motif_contestation: string;
  date_contestation: string | null;
}

export type ActionModeration = 'PUBLIER' | 'BLOQUER' | 'CLASSER';

export interface StatistiquesModeration {
  total: number;
  taux_blocage: number;
  faux_positifs: number;
  contestations: number;
  a_traiter: number;
  par_niveau: Record<string, number>;
}

export interface PublicationForumAdmin {
  id: number;
  pseudonyme: string;
  titre: string;
  contenu: string;
  thematique: string;
  thematique_affichee: string;
  date: string;
  statut_moderation: StatutModerationForum;
  decision_ia: DecisionIA | null;
}

export interface CommentaireForumAdmin {
  id: number;
  pseudonyme: string;
  publication: number;
  publication_titre: string;
  contenu: string;
  date: string;
  statut_moderation: StatutModerationForum;
  decision_ia: DecisionIA | null;
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
