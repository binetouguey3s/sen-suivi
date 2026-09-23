import { describe, expect, it } from 'vitest';

import { verifierMotDePasse } from './mot-de-passe';

describe('verifierMotDePasse', () => {
  it('refuse un mot de passe trop court', () => {
    expect(verifierMotDePasse('Ab1!xyz')).toContain('8 caractères');
  });

  it('refuse moins de trois catégories de caractères', () => {
    expect(verifierMotDePasse('dakarsenegal7')).toContain('trois');
  });

  it('refuse les suites évidentes et les répétitions', () => {
    for (const mdp of ['Teranga12345!', 'Azerty!Ngor7', 'Baobab!98765', 'Jammmm!2026']) {
      expect(verifierMotDePasse(mdp)).toContain('suites');
    }
  });

  it('accepte un mot de passe robuste', () => {
    for (const mdp of ['MotDePasse2026!', 'Teranga#Ngor7', 'baobab-du-sine-26', 'Liberty2026!']) {
      expect(verifierMotDePasse(mdp)).toBeNull();
    }
  });
});
