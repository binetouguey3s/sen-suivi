import { NomIcone } from '../icons/icons';
import { Ressource } from '../models/suivi';

export const ICONE_PAR_TYPE: Record<Ressource['type_ressource'], NomIcone> = {
  ARTICLE: 'article',
  EXERCICE: 'exercice',
  PODCAST: 'podcast',
};

export const LIBELLE_PAR_TYPE: Record<Ressource['type_ressource'], string> = {
  ARTICLE: 'Article',
  EXERCICE: 'Exercice',
  PODCAST: 'Podcast',
};

export function ajouteLe(dateIso: string): string {
  const jours = Math.round(
    (new Date().setHours(0, 0, 0, 0) - new Date(`${dateIso}T00:00:00`).getTime()) / 86_400_000,
  );
  if (jours <= 0) return "Ajouté aujourd'hui";
  if (jours === 1) return 'Ajouté hier';
  return `Ajouté il y a ${jours} jours`;
}

// Découpe le contenu (« ## » intertitre, « > » citation, ligne vide entre paragraphes)
// en blocs affichables, sans jamais injecter de HTML.
export type BlocContenu =
  | { genre: 'titre'; texte: string; id: string }
  | { genre: 'citation'; texte: string }
  | { genre: 'paragraphe'; texte: string };

export function decouperContenu(contenu: string): BlocContenu[] {
  return contenu
    .split(/\n\s*\n/)
    .map((b) => b.trim())
    .filter(Boolean)
    .map((bloc, i): BlocContenu => {
      if (bloc.startsWith('## ')) return { genre: 'titre', texte: bloc.slice(3), id: `section-${i}` };
      if (bloc.startsWith('> ')) return { genre: 'citation', texte: bloc.slice(2) };
      return { genre: 'paragraphe', texte: bloc };
    });
}
