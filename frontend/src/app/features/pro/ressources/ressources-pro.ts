// Libellés partagés par la liste « Mes ressources » et l'éditeur du professionnel.

import { NomIcone } from '../../../core/icons/icons';
import { Ressource, StatutRessource, TypeRessource } from '../../../core/models/suivi';

export const STATUTS: Record<StatutRessource, { libelle: string; onglet: string; classe: string }> = {
  PUBLIEE: { libelle: 'Publiée', onglet: 'Publiées', classe: 'publiee' },
  EN_ATTENTE: { libelle: 'En attente', onglet: 'En attente', classe: 'attente' },
  BROUILLON: { libelle: 'Brouillon', onglet: 'Brouillons', classe: 'brouillon' },
  REFUSEE: { libelle: 'À corriger', onglet: 'À corriger', classe: 'refusee' },
};
export const ORDRE_STATUTS: StatutRessource[] = ['PUBLIEE', 'EN_ATTENTE', 'BROUILLON', 'REFUSEE'];

export const FORMATS: { valeur: TypeRessource; libelle: string; aide: string; icone: NomIcone }[] = [
  { valeur: 'ARTICLE', libelle: 'Article', aide: 'Un texte à lire', icone: 'article' },
  { valeur: 'EXERCICE', libelle: 'Exercice', aide: 'Une pratique guidée', icone: 'exercice' },
  { valeur: 'PODCAST', libelle: 'Podcast', aide: 'Un fichier audio', icone: 'podcast' },
  { valeur: 'VIDEO', libelle: 'Vidéo', aide: 'Un lien YouTube', icone: 'video' },
];

export function format(type: TypeRessource) {
  return FORMATS.find((f) => f.valeur === type) ?? FORMATS[0];
}

// Thématiques proposées si la bibliothèque n'en a encore aucune
export const THEMATIQUES_PAR_DEFAUT = [
  'Stress', 'Respiration', 'Sommeil', 'Émotions', 'Travail', 'Études', 'Confiance en soi',
  'Famille', 'Relations', 'Motivation', 'Deuil', 'Bien-être',
];

export function initiales(nom: string): string {
  return nom
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((mot) => mot[0].toUpperCase())
    .join('');
}

const FORMAT_DATE: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' };

export function dateCourte(iso: string): string {
  return new Date(iso.length === 10 ? `${iso}T00:00:00` : iso).toLocaleDateString('fr-FR', FORMAT_DATE);
}

// « aujourd'hui », « hier », sinon la date
export function quand(iso: string, maintenant = new Date()): string {
  const jour = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const ecart = Math.round((jour(maintenant) - jour(new Date(iso))) / 86_400_000);
  if (ecart === 0) return 'aujourd’hui';
  if (ecart === 1) return 'hier';
  return `le ${dateCourte(iso)}`;
}

// Date affichée sur une ligne, selon le statut
export function dateDeLigne(r: Ressource): string {
  switch (r.statut) {
    case 'PUBLIEE':
      return `Publiée le ${dateCourte(r.date_publication)}`;
    case 'EN_ATTENTE':
      return r.date_soumission ? `Soumise le ${dateCourte(r.date_soumission)}` : 'En attente de relecture';
    case 'REFUSEE':
      return r.date_modification ? `Relue ${quand(r.date_modification)}` : 'À corriger';
    default:
      return r.date_modification ? `Modifiée ${quand(r.date_modification)}` : 'Brouillon';
  }
}

// Le chapô est le premier paragraphe du contenu (comme sur la page de la ressource)
export function separerChapo(contenu: string): { chapo: string; texte: string } {
  const blocs = contenu.trim().split(/\n\s*\n/);
  const premier = blocs[0] ?? '';
  if (!premier || /^(#|>|-\s)/.test(premier)) return { chapo: '', texte: contenu.trim() };
  return { chapo: premier.trim(), texte: blocs.slice(1).join('\n\n').trim() };
}

export function assemblerContenu(chapo: string, texte: string): string {
  return [chapo.trim(), texte.trim()].filter(Boolean).join('\n\n');
}
