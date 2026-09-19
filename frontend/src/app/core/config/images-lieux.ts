// Correspondance entre le nom d'un LieuDetente (API) et sa photo réelle
// (docs/CREDITS-IMAGES.md pour les crédits). Tous les lieux n'ont pas encore
// de photo : absent de cette table = pas d'image affichée, jamais de photo
// non sénégalaise en remplacement.
export const IMAGE_PAR_LIEU: Record<string, string> = {
  'Plage de Ngor': '/images/lieux/lieu-ngor.webp',
  'Lac Rose': '/images/lieux/lieu-lac-rose.webp',
  'Lagune de la Somone': '/images/lieux/lieu-somone.webp',
  'Parc Forestier de Hann': '/images/lieux/lieu-hann.webp',
};
