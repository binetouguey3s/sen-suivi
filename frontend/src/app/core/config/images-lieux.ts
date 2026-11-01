// Correspondance entre le nom d'un LieuDetente (API) et sa photo réelle
// (docs/CREDITS-IMAGES.md pour les crédits). Absent de cette table = pas
// d'image affichée, jamais de photo non sénégalaise en remplacement.
export const IMAGE_PAR_LIEU: Record<string, string> = {
  'Plages publiques (Ngor, Yoff, Virage, Anse Bernard, Malibu)': '/images/lieux/lieu-ngor.webp',
  'Lac Rose (Lac Retba)': '/images/lieux/lieu-lac-rose.webp',
  'Lagune de la Somone (RNIC)': '/images/lieux/lieu-somone.webp',
  'Parc Forestier et Zoologique de Hann': '/images/lieux/lieu-hann.webp',
  'Corniche Ouest & parcours sportifs': '/images/lieux/lieu-corniche-ouest.webp',
  'Île de Gorée': '/images/lieux/lieu-goree.webp',
  'Réserve Naturelle de Popenguine': '/images/lieux/lieu-popenguine.webp',
  'Toubab Dialaw': '/images/lieux/lieu-toubab-dialaw.webp',
};

// Nom comparé sans majuscules, accents ni espaces superflus : « lac rose (lac retba) »
// saisi dans l'administration retrouve la photo du « Lac Rose (Lac Retba) »
function cle(nom: string): string {
  return nom.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

const IMAGE_PAR_CLE = new Map(Object.entries(IMAGE_PAR_LIEU).map(([nom, image]) => [cle(nom), image]));

// Une photo envoyée par l'administration passe avant celle livrée avec le front-end
export function imageDuLieu(lieu: { nom: string; image: string | null }): string | null {
  return lieu.image ?? IMAGE_PAR_CLE.get(cle(lieu.nom)) ?? null;
}
