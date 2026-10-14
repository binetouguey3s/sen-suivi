import { describe, expect, it } from 'vitest';

import { NOTE_MAX, PHRASES_POUR_COMMENCER, ajouterDebut, phrasesDuJour } from './phrases';

describe('Phrases pour commencer', () => {
  it('trois phrases différentes, tirées de la liste', () => {
    const phrases = phrasesDuJour(new Date(2026, 9, 14, 9));
    expect(phrases).toHaveLength(3);
    expect(new Set(phrases).size).toBe(3);
    expect(phrases.every((p) => PHRASES_POUR_COMMENCER.includes(p))).toBe(true);
  });

  it('les mêmes toute la journée', () => {
    expect(phrasesDuJour(new Date(2026, 9, 14, 7))).toEqual(phrasesDuJour(new Date(2026, 9, 14, 23, 59)));
  });

  it('le tirage change au fil des jours', () => {
    const tirages = new Set(Array.from({ length: 10 }, (_, i) => phrasesDuJour(new Date(2026, 9, 1 + i)).join('|')));
    expect(tirages.size).toBeGreaterThan(1);
  });

  it('insère le début de phrase, prêt à être complété', () => {
    expect(ajouterDebut('', 'Je remercie…')).toBe('Je remercie ');
    expect(ajouterDebut('Bonne journée.', 'Demain, j’aimerais…')).toBe('Bonne journée.\nDemain, j’aimerais ');
    expect(ajouterDebut('Bonne journée.\n', 'Je remercie…')).toBe('Bonne journée.\nJe remercie ');
  });

  it('ne dépasse jamais la limite de la note', () => {
    expect(ajouterDebut('a'.repeat(NOTE_MAX - 3), 'Je remercie…')).toHaveLength(NOTE_MAX);
    expect(NOTE_MAX).toBe(1000);
  });
});
