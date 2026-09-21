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
});
