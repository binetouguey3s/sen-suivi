// Correspondance entre le nom d'un LieuDetente (API) et sa photo réelle
// (docs/CREDITS-IMAGES.md pour les crédits). Absent de cette table = pas
// d'image affichée, jamais de photo non sénégalaise en remplacement.
export const IMAGE_PAR_LIEU: Record<string, string> = {
  'Plage de Ngor': '/images/lieux/lieu-ngor.webp',
  'Lac Rose': '/images/lieux/lieu-lac-rose.webp',
  'Lagune de la Somone': '/images/lieux/lieu-somone.webp',
  'Parc Forestier de Hann': '/images/lieux/lieu-hann.webp',
  'Corniche Ouest': '/images/lieux/lieu-corniche-ouest.webp',
  'Île de Gorée': '/images/lieux/lieu-goree.webp',
  Popenguine: '/images/lieux/lieu-popenguine.webp',
  'Toubab Dialaw': '/images/lieux/lieu-toubab-dialaw.webp',
};

// Nom comparé sans majuscules, accents ni espaces superflus : « lac rose »
// saisi dans l'administration retrouve la photo du « Lac Rose »
function cle(nom: string): string {
  return nom.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

const IMAGE_PAR_CLE = new Map(Object.entries(IMAGE_PAR_LIEU).map(([nom, image]) => [cle(nom), image]));

export function imageDuLieu(nom: string): string | null {
  return IMAGE_PAR_CLE.get(cle(nom)) ?? null;
}
