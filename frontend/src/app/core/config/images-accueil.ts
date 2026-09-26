// Photos de la page d'accueil. Tant qu'une photo vaut null, la page affiche
// à sa place un fond aux couleurs de la charte. Chaque photo ajoutée doit
// être créditée dans docs/CREDITS-IMAGES.md.
export const IMAGES_ACCUEIL: Record<
  'bandeau' | 'stress' | 'anxiete' | 'fatigue' | 'fonctionnement' | 'appel',
  string | null
> = {
  bandeau: '/images/accueil/bandeau.webp',
  stress: '/images/accueil/stress.webp',
  anxiete: '/images/accueil/anxiete.webp',
  fatigue: '/images/accueil/fatigue.webp',
  fonctionnement: '/images/accueil/fonctionnement.webp',
  appel: '/images/accueil/appel.webp',
};
