// Types du volet orientation (apps/orientation côté Django).

export interface ProfessionnelPublic {
  id: number;
  nom: string;
  specialite: string;
  specialite_affichee: string;
  ville: string;
  langue: string;
  tarif_indicatif: number;
  presentation: string;
  domaines: string[];
  consultation_cabinet: boolean;
  adresse_cabinet: string;
  consultation_distance: boolean;
  accepte_demandes: boolean;
}

// GET /api/orientation/suggestion : UN professionnel mis en avant, puis tous les autres
export interface SuggestionOrientation {
  suggestion: { professionnel: ProfessionnelPublic; raison: string; besoins: string[] } | null;
  professionnels: ProfessionnelPublic[];
}

// Professionnel proposé par Titou dans le chatbot
export interface ProfessionnelSuggereChatbot {
  id: number;
  nom: string;
  specialite_affichee: string;
  ville: string;
  raison: string;
}

// GET /api/acces/etat
export interface EtatAcces {
  urgence: boolean;
  offre_active: boolean;
  jours_restants: number | null;
  verrouille: boolean;
  tarif_fcfa: number | null;
  duree_acces_jours?: number | null;
}

export type MoyenPaiement = 'WAVE' | 'ORANGE_MONEY' | 'FREE_MONEY';
