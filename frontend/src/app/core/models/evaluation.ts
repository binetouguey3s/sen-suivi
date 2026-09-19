// Types correspondant à apps/suivi (questions, auto-évaluation) et apps/comptes.

export type TypeEvaluation = 'STRESS' | 'ANXIETE' | 'FATIGUE';

export const LIBELLE_TYPE_EVALUATION: Record<TypeEvaluation, string> = {
  STRESS: 'de stress',
  ANXIETE: "d'anxiété",
  FATIGUE: 'de fatigue',
};

export function estTypeEvaluation(valeur: string | null | undefined): valeur is TypeEvaluation {
  return valeur === 'STRESS' || valeur === 'ANXIETE' || valeur === 'FATIGUE';
}

export interface OptionReponse {
  id: number;
  libelle: string;
  valeur: number;
}

export interface QuestionEvaluation {
  id: number;
  libelle: string;
  ordre: number;
  options: OptionReponse[];
}

export interface ProfessionnelSuggere {
  id: number;
  nom: string;
  specialite_affichee: string;
  ville: string;
  langue: string;
  tarif_indicatif: number;
}

export interface ResultatEvaluation {
  id: number;
  type_evaluation: TypeEvaluation;
  score_de_tendance: number;
  interpretation: string; // « Niveau faible » | « Niveau modéré » | « Niveau élevé »
  texte_interpretation: string;
  avertissement: string;
  professionnels_suggeres: ProfessionnelSuggere[];
  message: string;
}
