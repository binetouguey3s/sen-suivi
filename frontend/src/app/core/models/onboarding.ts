// Réponses enregistrées dans preferences.onboarding (PATCH /api/comptes/moi).
// Aucun champ n'est obligatoire : une réponse absente reste simplement absente.
export interface ProfilOnboarding {
  version: 1;
  statut: 'termine' | 'passe';
  date: string;
  genre?: string;
  tranche_age?: string;
  situation?: string;
  langue?: string;
  humeur?: number;
  energie?: number;
  sommeil?: string;
  preoccupations: string[];
  rien_de_particulier: boolean;
  bien_etre: string[];
  spiritualite: string[];
  moments: string[];
  duree?: string;
  formats: string[];
  rappels: boolean;
  frequence_rappels?: string;
  echange_pro?: string;
  metiers: string[];
  aise_avec?: string;
}
