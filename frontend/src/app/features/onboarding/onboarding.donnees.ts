// Onboarding de personnalisation : contenus et listes de choix.
// Toutes les réponses sont facultatives ; elles servent uniquement à adapter
// le ton de Titou et les contenus proposés (positionnement bien-être, non clinique).

import { NomIcone } from '../../core/icons/icons';

export interface Choix<T extends string = string> {
  valeur: T;
  libelle: string;
  icone?: NomIcone;
  aide?: string;
}

// ─── Écrans ────────────────────────────────────────────────────────────────

export type Ecran = 'splash' | 'intro' | 'profil' | 'humeur' | 'esprit' | 'bien-etre' | 'rythme' | 'accompagnement' | 'pret';

export interface InfoEcran {
  photo: string;
  alt: string;
  // Cadrage de la photo dans le bandeau mobile (object-position)
  cadrage: string;
  // Libellé posé sur la photo, pour les 6 étapes
  libelle?: string;
  icone?: NomIcone;
}

export const ETAPES: readonly Ecran[] = ['profil', 'humeur', 'esprit', 'bien-etre', 'rythme', 'accompagnement'];
export const ORDRE: readonly Ecran[] = ['splash', 'intro', ...ETAPES, 'pret'];

const DOSSIER = '/images/onboarding/';

export const ECRANS: Record<Ecran, InfoEcran> = {
  splash: {
    photo: `${DOSSIER}splash.webp`,
    alt: 'Une jeune femme sourit au milieu de fleurs blanches',
    cadrage: 'center 30%',
  },
  intro: {
    photo: `${DOSSIER}bienvenue.webp`,
    alt: 'Une jeune femme, les yeux fermés, savoure le soleil dans un champ',
    cadrage: 'center 15%',
  },
  profil: {
    photo: `${DOSSIER}profil.webp`,
    alt: 'Une jeune femme souriante regarde son téléphone, un casque autour du cou',
    cadrage: 'center 0%',
    libelle: 'Ton profil',
    icone: 'utilisateur',
  },
  humeur: {
    photo: `${DOSSIER}humeur.webp`,
    alt: 'Une jeune femme lit, assise au pied d’un arbre',
    cadrage: 'center 45%',
    libelle: 'Ton humeur',
    icone: 'suggestion',
  },
  esprit: {
    photo: `${DOSSIER}esprit.webp`,
    alt: 'Un jeune homme avec un casque révise en plein air',
    cadrage: 'center 10%',
    libelle: 'Tes préoccupations',
    icone: 'suggestion',
  },
  'bien-etre': {
    photo: `${DOSSIER}bien-etre.webp`,
    alt: 'Un jeune homme se détend allongé dans l’herbe, un casque sur les oreilles',
    cadrage: 'center 50%',
    libelle: 'Tes envies',
    icone: 'coeur',
  },
  rythme: {
    photo: `${DOSSIER}rythme.webp`,
    alt: 'Coucher de soleil sur la mer',
    cadrage: 'center 50%',
    libelle: 'Ton rythme',
    icone: 'horloge',
  },
  accompagnement: {
    photo: `${DOSSIER}accompagnement.webp`,
    alt: 'Des mains forment ensemble un cœur',
    cadrage: 'center 40%',
    libelle: 'Accompagnement',
    icone: 'accompagnement',
  },
  pret: {
    photo: `${DOSSIER}pret.webp`,
    alt: 'Une personne lève les bras face au soleil couchant',
    cadrage: 'center 35%',
  },
};

// ─── Étape 1 : profil ──────────────────────────────────────────────────────

export const GENRES: readonly Choix[] = [
  { valeur: 'femme', libelle: 'Une femme' },
  { valeur: 'homme', libelle: 'Un homme' },
  { valeur: 'non_precise', libelle: 'Je préfère ne pas répondre' },
];

export const TRANCHES_AGE: readonly Choix[] = [
  { valeur: '15-17', libelle: '15–17 ans' },
  { valeur: '18-24', libelle: '18–24 ans' },
  { valeur: '25-30', libelle: '25–30 ans' },
  { valeur: '31-35', libelle: '31–35 ans' },
  { valeur: '35+', libelle: 'Plus de 35 ans' },
];

export const SITUATIONS: readonly Choix[] = [
  { valeur: 'eleve', libelle: 'Collégien·ne ou lycéen·ne' },
  { valeur: 'etudiant', libelle: 'Étudiant·e' },
  { valeur: 'emploi', libelle: 'En emploi' },
  { valeur: 'recherche', libelle: 'En recherche d’emploi' },
  { valeur: 'entrepreneur', libelle: 'Entrepreneur·e' },
  { valeur: 'autre', libelle: 'Autre' },
];

export const LANGUES: readonly Choix[] = [
  { valeur: 'fr', libelle: 'Français' },
  { valeur: 'wo', libelle: 'Wolof' },
  { valeur: 'les_deux', libelle: 'Les deux' },
];

// ─── Étape 2 : humeur ──────────────────────────────────────────────────────

export const HUMEURS: readonly (Choix & { note: number })[] = [
  { valeur: '1', note: 1, libelle: 'Très bas', icone: 'humeur-1' },
  { valeur: '2', note: 2, libelle: 'Bas', icone: 'humeur-2' },
  { valeur: '3', note: 3, libelle: 'Neutre', icone: 'humeur-3' },
  { valeur: '4', note: 4, libelle: 'Bien', icone: 'humeur-4' },
  { valeur: '5', note: 5, libelle: 'Très bien', icone: 'humeur-5' },
];

export const SOMMEILS: readonly Choix[] = [
  { valeur: 'bien', libelle: 'Je dors bien', icone: 'lune' },
  { valeur: 'irregulier', libelle: 'C’est irrégulier', icone: 'lune' },
  { valeur: 'difficile', libelle: 'J’ai du mal à dormir', icone: 'lune' },
];

// ─── Étape 3 : ce qui occupe l'esprit ──────────────────────────────────────

export const MAX_PREOCCUPATIONS = 3;

export const PREOCCUPATIONS: readonly Choix[] = [
  { valeur: 'stress', libelle: 'Stress' },
  { valeur: 'etudes', libelle: 'Études et examens' },
  { valeur: 'travail', libelle: 'Travail' },
  { valeur: 'sommeil', libelle: 'Sommeil' },
  { valeur: 'emotions', libelle: 'Émotions' },
  { valeur: 'confiance', libelle: 'Confiance en soi' },
  { valeur: 'motivation', libelle: 'Motivation' },
  { valeur: 'famille', libelle: 'Famille' },
  { valeur: 'relations', libelle: 'Relations' },
  { valeur: 'solitude', libelle: 'Solitude' },
  { valeur: 'deuil', libelle: 'Deuil' },
  { valeur: 'organisation', libelle: 'Organisation' },
  { valeur: 'ecrans', libelle: 'Écrans et réseaux' },
  { valeur: 'avenir', libelle: 'L’avenir' },
];

// ─── Étape 4 : ce qui fait du bien ─────────────────────────────────────────

export const BIEN_ETRE: readonly Choix[] = [
  { valeur: 'musique', libelle: 'Musique', icone: 'musique' },
  { valeur: 'spiritualite', libelle: 'Spiritualité et prière', icone: 'spiritualite' },
  { valeur: 'meditation', libelle: 'Méditation', icone: 'meditation' },
  { valeur: 'respiration', libelle: 'Respiration', icone: 'respirer' },
  { valeur: 'yoga', libelle: 'Yoga et étirements', icone: 'yoga' },
  { valeur: 'sport', libelle: 'Sport et marche', icone: 'marche' },
  { valeur: 'lecture', libelle: 'Lecture', icone: 'ressources' },
  { valeur: 'ecriture', libelle: 'Écriture', icone: 'stylo' },
  { valeur: 'podcasts', libelle: 'Podcasts', icone: 'ecouter' },
  { valeur: 'nature', libelle: 'Nature et plage', icone: 'nature' },
  { valeur: 'proche', libelle: 'Parler à un proche', icone: 'chat' },
  { valeur: 'creer', libelle: 'Créer', icone: 'creer' },
];

export const SPIRITUALITE: readonly Choix[] = [
  { valeur: 'coran', libelle: 'Récitation du Coran' },
  { valeur: 'khassaides', libelle: 'Khassaïdes' },
  { valeur: 'dhikr', libelle: 'Dhikr et invocations' },
  { valeur: 'priere_chretienne', libelle: 'Prière chrétienne et louange' },
  { valeur: 'chants', libelle: 'Chants religieux' },
  { valeur: 'autre', libelle: 'Autre' },
];

// ─── Étape 5 : rythme ──────────────────────────────────────────────────────

export const MOMENTS: readonly Choix[] = [
  { valeur: 'matin', libelle: 'Le matin' },
  { valeur: 'midi', libelle: 'À midi' },
  { valeur: 'soir', libelle: 'Le soir' },
  { valeur: 'coucher', libelle: 'Avant de dormir' },
];

export const DUREES: readonly Choix[] = [
  { valeur: '2', libelle: '2 min', aide: 'Une pause' },
  { valeur: '5-10', libelle: '5–10 min', aide: 'Un vrai moment' },
  { valeur: '15+', libelle: '15 min +', aide: 'Une séance' },
];

export const FORMATS: readonly Choix[] = [
  { valeur: 'texte', libelle: 'Texte' },
  { valeur: 'audio', libelle: 'Audio' },
  { valeur: 'video', libelle: 'Vidéo' },
  { valeur: 'exercice', libelle: 'Exercice guidé' },
];

export const FREQUENCES: readonly Choix[] = [
  { valeur: 'quotidien', libelle: 'Chaque jour' },
  { valeur: '3_semaine', libelle: '3× / semaine' },
  { valeur: 'jamais', libelle: 'Jamais' },
];

// ─── Étape 6 : accompagnement ──────────────────────────────────────────────

export const ECHANGES_PRO: readonly Choix[] = [
  { valeur: 'pas_maintenant', libelle: 'Pas pour l’instant', icone: 'horloge' },
  { valeur: 'plus_tard', libelle: 'Peut-être plus tard', icone: 'chat' },
  { valeur: 'oui', libelle: 'Oui, j’aimerais bien', icone: 'proche' },
];

// Les six métiers du bien-être de la plateforme (mêmes valeurs que SpecialitePro)
export const METIERS: readonly Choix[] = [
  { valeur: 'PSYCHOLOGUE', libelle: 'Psychologue' },
  { valeur: 'ASSISTANT_SOCIAL', libelle: 'Assistant·e social·e' },
  { valeur: 'COACH_DEVELOPPEMENT', libelle: 'Coach en développement personnel' },
  { valeur: 'SOPHROLOGUE', libelle: 'Sophrologue' },
  { valeur: 'MEDIATEUR_FAMILIAL', libelle: 'Médiateur·rice familial·e' },
  { valeur: 'COACH_SPORTIF', libelle: 'Coach sportif' },
];

export const AISANCES: readonly Choix[] = [
  { valeur: 'femme', libelle: 'Une femme' },
  { valeur: 'homme', libelle: 'Un homme' },
  { valeur: 'indifferent', libelle: 'Peu importe' },
];

// ─── Écran final : premières ressources ────────────────────────────────────

export interface Suggestion {
  titre: string;
  meta: string;
  image: string;
  // Préoccupations ou envies qui font remonter la suggestion
  pour: readonly string[];
}

export const SUGGESTIONS: readonly Suggestion[] = [
  {
    titre: 'Respiration guidée du soir',
    meta: '3 min · Audio',
    image: `${DOSSIER}ressource-respiration.webp`,
    pour: ['stress', 'sommeil', 'respiration', 'soir', 'coucher'],
  },
  {
    titre: 'Gérer le stress des examens',
    meta: '5 min · Article',
    image: `${DOSSIER}ressource-examens.webp`,
    pour: ['etudes', 'stress', 'organisation', 'motivation'],
  },
  {
    titre: 'Méditation apaisante pour s’endormir',
    meta: '10 min · Audio',
    image: `${DOSSIER}ressource-sommeil.webp`,
    pour: ['sommeil', 'meditation', 'emotions', 'coucher'],
  },
];
