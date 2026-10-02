// Visuel de chaque ressource : une photo par thématique (originaux dans
// images-brutes/images-ressources, crédits dans docs/CREDITS-IMAGES.md), sinon une
// illustration du sprite public/images/ressources/illustrations.svg, dessinée avec
// les variables de la charte. Une ressource sans l'un ni l'autre garde l'icône
// de son format.
const PAR_TITRE: Record<string, string> = {
  'Cinq minutes pour respirer avant un examen': 'respiration-examen',
  'Exercice de respiration guidée, 4 minutes': 'respiration-guidee',
  'Gérer la pression familiale sans culpabiliser': 'famille',
  "La charge mentale des étudiantes à l'UCAD": 'etudes',
  'Dormir mieux quand on travaille en horaires décalés': 'sommeil',
  'Retrouver le calme après une journée dans les embouteillages': 'stress-trafic',
  "Parler de ce qu'on ressent, même quand ça ne se fait pas": 'expression',
  'Podcast : la teranga commence par soi-même': 'podcast',
  'Tenir une échéance au travail sans s’épuiser': 'travail-echeance',
  'Reprendre confiance en soi, pas à pas': 'confiance',
  'Se sentir seul, même entouré': 'solitude',
  'Quand tout s’accumule : organiser sa semaine': 'organisation',
  'Prendre la parole sans paniquer': 'prise-de-parole',
  'Quand la colère monte': 'colere',
  'Traverser une rupture amoureuse': 'rupture',
  'Traverser la perte d’un proche': 'deuil',
  'Réseaux sociaux : arrêter de se comparer': 'reseaux-sociaux',
  'Garder le moral pendant la recherche d’emploi': 'recherche-emploi',
  'Quand l’envie n’est plus là': 'motivation',
  'Trois minutes pour décompresser au travail': 'pause-travail',
};

const PAR_THEMATIQUE: Record<string, string> = {
  respiration: 'respiration-guidee',
  famille: 'famille',
  etudes: 'etudes',
  sommeil: 'sommeil',
  stress: 'stress-trafic',
  expression: 'expression',
  'bien-etre': 'bien-etre',
  travail: 'travail-echeance',
  'confiance en soi': 'confiance',
  'lien social': 'solitude',
  organisation: 'organisation',
  emotions: 'colere',
  relations: 'rupture',
  deuil: 'deuil',
  numerique: 'reseaux-sociaux',
  motivation: 'motivation',
};

const SPRITE = '/images/ressources/illustrations.svg';

// « contenir » : image sur fond blanc (pictogramme, objet détouré) affichée entière ;
// sinon la photo remplit le bandeau, cadrée sur `position`.
interface Photo {
  fichier: string;
  contenir?: boolean;
  position?: string;
}

const PHOTO_PAR_THEMATIQUE: Record<string, Photo> = {
  'bien-etre': { fichier: 'bien-etre', position: 'center 70%' },
  'confiance en soi': { fichier: 'confiance', position: 'center 35%' },
  deuil: { fichier: 'deuil' },
  emotions: { fichier: 'emotions', contenir: true },
  etudes: { fichier: 'etudes' },
  famille: { fichier: 'famille', contenir: true },
  'lien social': { fichier: 'lien-social' },
  motivation: { fichier: 'motivation' },
  numerique: { fichier: 'numerique' },
  organisation: { fichier: 'organisation' },
  relations: { fichier: 'relations' },
  respiration: { fichier: 'respiration' },
  sommeil: { fichier: 'sommeil' },
  stress: { fichier: 'stress', position: 'center 75%' },
  travail: { fichier: 'travail', contenir: true },
};

// Le titre l'emporte sur la thématique quand il nomme l'image
const PHOTO_PAR_TITRE: Record<string, Photo> = {
  'Podcast : la teranga commence par soi-même': { fichier: 'podcast', contenir: true },
};

export type VisuelRessource =
  | { genre: 'photo'; src: string; contenir: boolean; position: string }
  | { genre: 'illustration'; href: string };

// Comparaison sans majuscules, accents ni apostrophes typographiques
function cle(texte: string): string {
  return texte
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[’']/g, "'")
    .toLowerCase()
    .trim();
}

const PHOTOS_TITRES = new Map(Object.entries(PHOTO_PAR_TITRE).map(([titre, photo]) => [cle(titre), photo]));
const PHOTOS_THEMATIQUES = new Map(Object.entries(PHOTO_PAR_THEMATIQUE).map(([theme, photo]) => [cle(theme), photo]));
const TITRES = new Map(Object.entries(PAR_TITRE).map(([titre, id]) => [cle(titre), id]));
const THEMATIQUES = new Map(Object.entries(PAR_THEMATIQUE).map(([theme, id]) => [cle(theme), id]));

export function illustrationRessource(titre: string, thematique: string): string | null {
  const id = TITRES.get(cle(titre)) ?? THEMATIQUES.get(cle(thematique));
  return id ? `${SPRITE}#${id}` : null;
}

export function visuelRessource(titre: string, thematique: string): VisuelRessource | null {
  const photo = PHOTOS_TITRES.get(cle(titre)) ?? PHOTOS_THEMATIQUES.get(cle(thematique));
  if (photo) {
    return {
      genre: 'photo',
      src: `/images/ressources/ressource-${photo.fichier}.webp`,
      contenir: !!photo.contenir,
      position: photo.position ?? 'center',
    };
  }
  const href = illustrationRessource(titre, thematique);
  return href ? { genre: 'illustration', href } : null;
}
