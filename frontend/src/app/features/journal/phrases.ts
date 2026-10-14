// « Phrases pour commencer » du journal : des débuts de phrase à compléter,
// pour aider à écrire. Trois au hasard, les mêmes toute la journée.
// La note reste privée : rien n'est envoyé à Titou.

import { jourDeLAnnee } from '../../core/utils/jour';

export const NOTE_MAX = 1000;
export const NOMBRE_PHRASES = 3;

export const PHRASES_POUR_COMMENCER: readonly string[] = [
  'Aujourd’hui, ce qui m’a fait du bien…',
  'Une chose dont je suis fier·e…',
  'Ce qui me pèse en ce moment…',
  'Demain, j’aimerais…',
  'Je remercie…',
];

// Tirage déterministe : la graine est la date, le mélange change chaque jour
export function phrasesDuJour(date: Date, nombre = NOMBRE_PHRASES): string[] {
  let graine = date.getFullYear() * 1000 + jourDeLAnnee(date);
  const hasard = () => {
    graine = (graine * 1103515245 + 12345) % 2147483648;
    return graine / 2147483648;
  };
  const melange = [...PHRASES_POUR_COMMENCER];
  for (let i = melange.length - 1; i > 0; i--) {
    const j = Math.floor(hasard() * (i + 1));
    [melange[i], melange[j]] = [melange[j], melange[i]];
  }
  return melange.slice(0, nombre);
}

// Ajoute le début de phrase à la note (sur une nouvelle ligne si elle n'est pas
// vide), sans les points de suspension, prêt à être complété. Jamais au-delà de NOTE_MAX.
export function ajouterDebut(note: string, phrase: string): string {
  const debut = `${phrase.replace(/…$/, '').trimEnd()} `;
  const separateur = note.trim() ? (note.endsWith('\n') ? '' : '\n') : '';
  return `${note.trim() ? note : ''}${separateur}${debut}`.slice(0, NOTE_MAX);
}
