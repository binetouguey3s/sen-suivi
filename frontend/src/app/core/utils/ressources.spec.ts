import { describe, expect, it } from 'vitest';

import { decouperContenu } from './ressources';
import { valeurs } from './ressource';

describe('decouperContenu', () => {
  it('découpe titres, citations et paragraphes sans injecter de HTML', () => {
    const blocs = decouperContenu('## Titre\n\nUn paragraphe.\n\n> Une citation');
    expect(blocs.map((b) => b.genre)).toEqual(['titre', 'paragraphe', 'citation']);
  });

  it('ignore les blocs vides', () => {
    expect(decouperContenu('\n\n  \n\n')).toEqual([]);
  });
});

describe('valeurs', () => {
  it("renvoie une liste vide quand la ressource n'a pas de valeur (état d'erreur)", () => {
    expect(valeurs({ hasValue: () => false, value: () => { throw new Error('erreur'); } })).toEqual([]);
  });

  it('renvoie la valeur quand elle existe', () => {
    expect(valeurs({ hasValue: () => true, value: () => [1, 2] })).toEqual([1, 2]);
  });

  it('un intertitre peut être suivi de son texte sans ligne vide', () => {
    const blocs = decouperContenu('## 1. Respirer\nInspirez sur quatre temps.\n> Tout va bien.');
    expect(blocs).toEqual([
      { genre: 'titre', texte: '1. Respirer', id: 'section-0' },
      { genre: 'paragraphe', texte: 'Inspirez sur quatre temps.' },
      { genre: 'citation', texte: 'Tout va bien.' },
    ]);
  });

  it('les lignes « - » deviennent une liste', () => {
    const [liste] = decouperContenu('- Un seul sujet\n- Des étapes courtes');
    expect(liste).toMatchObject({ genre: 'liste', elements: ['Un seul sujet', 'Des étapes courtes'] });
  });
});
