// Photos de la page d'accueil. Tant qu'une photo vaut null, la page affiche
// à sa place un fond aux couleurs de la charte. Chaque photo ajoutée doit
// être créditée dans docs/CREDITS-IMAGES.md.
export const IMAGES_ACCUEIL: Record<'stress' | 'anxiete' | 'fatigue' | 'fonctionnement' | 'appel', string | null> = {
  stress: '/images/accueil/stress.webp',
  anxiete: '/images/accueil/anxiete.webp',
  fatigue: '/images/accueil/fatigue.webp',
  fonctionnement: '/images/accueil/fonctionnement.webp',
  appel: '/images/accueil/appel.webp',
};

export interface DiapoBandeau {
  src: string;
  // Cadrage de la photo dans le bandeau (background-position)
  cadrage: string;
}

// Photos du bandeau d'ouverture, qui se succèdent en fondu
export const DIAPOS_BANDEAU: readonly DiapoBandeau[] = [
  { src: '/images/accueil/bandeau.webp', cadrage: 'center 30%' },
  { src: '/images/accueil/bandeau-2.webp', cadrage: 'center 62%' },
  { src: '/images/accueil/bandeau-3.webp', cadrage: 'center 30%' },
  { src: '/images/accueil/bandeau-4.webp', cadrage: 'center 30%' },
];

// Durée d'affichage de chaque photo du bandeau
export const DUREE_DIAPO_MS = 2000;
