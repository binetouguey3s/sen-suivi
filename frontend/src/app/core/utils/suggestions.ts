// Ressources « Pour vous » du tableau de bord : des règles simples et
// explicables, jamais d'IA. Chaque critère rapporte des points ; la raison
// affichée est celle du critère qui a le plus compté.
//   +3 la thématique répond à une préoccupation choisie dans l'onboarding
//   +2 humeur du jour basse, et un exercice qui apaise (Respiration, Bien-être)
//   +1 le format préféré
//   +1 la durée préférée
// Égalité : la plus récente. Sans consentement ou sans onboarding : les plus récentes.

import { PREOCCUPATIONS } from '../../features/onboarding/onboarding.donnees';
import { ProfilOnboarding } from '../models/onboarding';
import { NiveauHumeur, Ressource } from '../models/suivi';

export interface Suggestion {
  ressource: Ressource;
  raison: string;
  points: number;
}

export const NOMBRE_SUGGESTIONS = 3;
export const RAISON_NOUVEAUTE = 'Nouveauté';

// Préoccupation de l'onboarding → thématiques de la bibliothèque
const THEMATIQUES_PAR_PREOCCUPATION: Record<string, readonly string[]> = {
  stress: ['Stress', 'Respiration'],
  etudes: ['Études'],
  travail: ['Travail'],
  sommeil: ['Sommeil'],
  emotions: ['Émotions', 'Expression'],
  confiance: ['Confiance en soi'],
  motivation: ['Motivation'],
  famille: ['Famille'],
  relations: ['Relations', 'Lien social'],
  solitude: ['Lien social'],
  deuil: ['Deuil'],
  organisation: ['Organisation'],
  ecrans: ['Numérique'],
  avenir: ['Motivation'],
};

const HUMEURS_BASSES: readonly NiveauHumeur[] = ['TRES_MAL', 'MAL'];
const THEMATIQUES_APAISANTES = ['Respiration', 'Bien-être'];

const TYPE_PAR_FORMAT: Record<string, Ressource['type_ressource']> = {
  audio: 'PODCAST',
  exercice: 'EXERCICE',
  texte: 'ARTICLE',
};
const LIBELLE_FORMAT: Record<string, string> = { audio: 'audio', exercice: 'exercice guidé', texte: 'texte' };

// Durée préférée → minutes acceptées
const DUREE_CONVIENT: Record<string, (minutes: number) => boolean> = {
  '2': (m) => m <= 3,
  '5-10': (m) => m >= 4 && m <= 10,
  '15+': (m) => m >= 11,
};

function normaliser(texte: string): string {
  return texte.trim().toLowerCase();
}

function plusRecenteDabord(a: Ressource, b: Ressource): number {
  return b.date_publication.localeCompare(a.date_publication) || b.id - a.id;
}

interface Critere {
  points: number;
  raison: string;
}

function criteres(ressource: Ressource, profil: ProfilOnboarding, humeur: NiveauHumeur | null): Critere[] {
  const trouves: Critere[] = [];
  const thematique = normaliser(ressource.thematique);

  const preoccupation = (profil.preoccupations ?? []).find((p) =>
    (THEMATIQUES_PAR_PREOCCUPATION[p] ?? []).some((t) => normaliser(t) === thematique),
  );
  if (preoccupation) {
    const libelle = PREOCCUPATIONS.find((c) => c.valeur === preoccupation)?.libelle ?? ressource.thematique;
    trouves.push({ points: 3, raison: `Parce que vous avez choisi : ${libelle}` });
  }

  if (
    humeur &&
    HUMEURS_BASSES.includes(humeur) &&
    ressource.type_ressource === 'EXERCICE' &&
    THEMATIQUES_APAISANTES.some((t) => normaliser(t) === thematique)
  ) {
    trouves.push({ points: 2, raison: 'Pour vous apaiser aujourd’hui' });
  }

  const format = (profil.formats ?? []).find((f) => TYPE_PAR_FORMAT[f] === ressource.type_ressource);
  if (format) {
    trouves.push({ points: 1, raison: `Au format ${LIBELLE_FORMAT[format]}, comme vous aimez` });
  }

  if (profil.duree && DUREE_CONVIENT[profil.duree]?.(ressource.duree_lecture)) {
    trouves.push({ points: 1, raison: `En ${ressource.duree_lecture} min, le temps que vous vous accordez` });
  }
  return trouves;
}

export function suggererRessources(
  ressources: readonly Ressource[],
  profil: ProfilOnboarding | undefined,
  humeurDuJour: NiveauHumeur | null,
  consentement: boolean,
): Suggestion[] {
  const recentes = [...ressources].sort(plusRecenteDabord);
  if (!consentement || !profil) {
    return recentes.slice(0, NOMBRE_SUGGESTIONS).map((ressource) => ({ ressource, raison: RAISON_NOUVEAUTE, points: 0 }));
  }

  return recentes
    .map((ressource) => {
      const trouves = criteres(ressource, profil, humeurDuJour);
      // La raison affichée : le critère qui pèse le plus (le premier en cas d'égalité)
      const principal = trouves.reduce<Critere | null>((max, c) => (!max || c.points > max.points ? c : max), null);
      return {
        ressource,
        raison: principal?.raison ?? RAISON_NOUVEAUTE,
        points: trouves.reduce((total, c) => total + c.points, 0),
      };
    })
    .sort((a, b) => b.points - a.points || plusRecenteDabord(a.ressource, b.ressource))
    .slice(0, NOMBRE_SUGGESTIONS);
}
