import { NomIcone } from '../icons/icons';
import { Ressource } from '../models/suivi';

export const ICONE_PAR_TYPE: Record<Ressource['type_ressource'], NomIcone> = {
  ARTICLE: 'article',
  EXERCICE: 'exercice',
  PODCAST: 'podcast',
  VIDEO: 'video',
};

export const LIBELLE_PAR_TYPE: Record<Ressource['type_ressource'], string> = {
  ARTICLE: 'Article',
  EXERCICE: 'Exercice',
  PODCAST: 'Podcast',
  VIDEO: 'Vidéo',
};

export function ajouteLe(dateIso: string): string {
  const jours = Math.round(
    (new Date().setHours(0, 0, 0, 0) - new Date(`${dateIso}T00:00:00`).getTime()) / 86_400_000,
  );
  if (jours <= 0) return "Ajouté aujourd'hui";
  if (jours === 1) return 'Ajouté hier';
  return `Ajouté il y a ${jours} jours`;
}

// Découpe le contenu (« ## » intertitre, « > » citation, « - » liste, ligne
// vide entre paragraphes) en blocs affichables, sans jamais injecter de HTML.
// Ligne par ligne : un intertitre peut être directement suivi de son texte,
// comme l'écrivent les professionnels dans l'éditeur.
export type BlocContenu =
  | { genre: 'titre'; texte: string; id: string }
  | { genre: 'citation'; texte: string }
  | { genre: 'paragraphe'; texte: string }
  | { genre: 'liste'; texte: string; elements: string[] };

export function decouperContenu(contenu: string): BlocContenu[] {
  const blocs: BlocContenu[] = [];
  let lignes: string[] = [];
  let genre: 'paragraphe' | 'citation' | 'liste' | null = null;

  const fermer = () => {
    if (genre === 'liste') blocs.push({ genre, texte: lignes.join(' '), elements: lignes });
    else if (genre) blocs.push({ genre, texte: lignes.join(genre === 'citation' ? ' ' : '\n') });
    lignes = [];
    genre = null;
  };
  const ajouter = (nouveau: NonNullable<typeof genre>, texte: string) => {
    if (genre !== nouveau) fermer();
    genre = nouveau;
    lignes.push(texte);
  };

  for (const brute of contenu.split('\n')) {
    const ligne = brute.trim();
    if (!ligne) fermer();
    else if (ligne.startsWith('## ')) {
      fermer();
      blocs.push({ genre: 'titre', texte: ligne.slice(3).trim(), id: `section-${blocs.length}` });
    } else if (ligne.startsWith('> ')) ajouter('citation', ligne.slice(2).trim());
    else if (/^[-•]\s/.test(ligne)) ajouter('liste', ligne.slice(2).trim());
    else ajouter('paragraphe', ligne);
  }
  fermer();
  return blocs;
}
