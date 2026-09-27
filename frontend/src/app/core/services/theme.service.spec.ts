import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CLE_THEME, ThemeService } from './theme.service';

// Réglage clair / sombre de l'appareil, modifiable en cours de test
function simulerAppareil(sombre: boolean) {
  const ecouteurs = new Set<(e: MediaQueryListEvent) => void>();
  const requete = {
    matches: sombre,
    media: '(prefers-color-scheme: dark)',
    addEventListener: (_: string, f: (e: MediaQueryListEvent) => void) => ecouteurs.add(f),
    removeEventListener: (_: string, f: (e: MediaQueryListEvent) => void) => ecouteurs.delete(f),
  };
  vi.stubGlobal('matchMedia', () => requete);
  return {
    basculer(nouveau: boolean): void {
      requete.matches = nouveau;
      ecouteurs.forEach((f) => f({ matches: nouveau } as MediaQueryListEvent));
    },
  };
}

const themeAffiche = (): string | undefined => document.documentElement.dataset['theme'];

describe('ThemeService', () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset['theme'];
    document.documentElement.classList.remove('sans-transition');
    TestBed.resetTestingModule();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('suit l’appareil par défaut, sans rien enregistrer', () => {
    simulerAppareil(true);
    const service = TestBed.inject(ThemeService);

    expect(service.choix()).toBe('systeme');
    expect(service.applique()).toBe('sombre');
    expect(themeAffiche()).toBe('sombre');
    expect(localStorage.getItem(CLE_THEME)).toBeNull();
  });

  it('persiste le choix et l’applique à la page', () => {
    simulerAppareil(false);
    const service = TestBed.inject(ThemeService);

    service.choisir('sombre');

    expect(localStorage.getItem(CLE_THEME)).toBe('sombre');
    expect(service.choix()).toBe('sombre');
    expect(themeAffiche()).toBe('sombre');
  });

  it('restaure le choix enregistré au démarrage, même contre le réglage de l’appareil', () => {
    simulerAppareil(true);
    localStorage.setItem(CLE_THEME, 'clair');

    const service = TestBed.inject(ThemeService);

    expect(service.choix()).toBe('clair');
    expect(service.applique()).toBe('clair');
    expect(themeAffiche()).toBe('clair');
  });

  it('ignore une valeur enregistrée inconnue', () => {
    simulerAppareil(false);
    localStorage.setItem(CLE_THEME, 'violet');

    expect(TestBed.inject(ThemeService).choix()).toBe('systeme');
  });

  it('en mode système, suit le changement de préférence de l’appareil en direct', () => {
    const appareil = simulerAppareil(false);
    const service = TestBed.inject(ThemeService);
    expect(themeAffiche()).toBe('clair');

    appareil.basculer(true);
    expect(service.applique()).toBe('sombre');
    expect(themeAffiche()).toBe('sombre');

    appareil.basculer(false);
    expect(themeAffiche()).toBe('clair');
  });

  it('avec un choix explicite, ne suit plus l’appareil', () => {
    const appareil = simulerAppareil(false);
    const service = TestBed.inject(ThemeService);
    service.choisir('clair');

    appareil.basculer(true);

    expect(service.applique()).toBe('clair');
    expect(themeAffiche()).toBe('clair');
  });

  it('coupe les transitions pendant 200 ms à la bascule', () => {
    vi.useFakeTimers();
    simulerAppareil(false);
    const service = TestBed.inject(ThemeService);
    const racine = document.documentElement;
    expect(racine.classList.contains('sans-transition')).toBe(false);

    service.choisir('sombre');
    expect(racine.classList.contains('sans-transition')).toBe(true);

    vi.advanceTimersByTime(199);
    expect(racine.classList.contains('sans-transition')).toBe(true);
    vi.advanceTimersByTime(1);
    expect(racine.classList.contains('sans-transition')).toBe(false);
  });

  it('reste utilisable quand localStorage est indisponible', () => {
    simulerAppareil(false);
    const erreur = () => {
      throw new DOMException('Stockage bloqué', 'SecurityError');
    };
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(erreur);
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(erreur);

    const service = TestBed.inject(ThemeService);
    expect(service.choix()).toBe('systeme');

    expect(() => service.choisir('sombre')).not.toThrow();
    expect(service.choix()).toBe('sombre');
    expect(themeAffiche()).toBe('sombre');
  });

  it('fonctionne sans matchMedia (navigateur ancien)', () => {
    vi.stubGlobal('matchMedia', undefined);

    const service = TestBed.inject(ThemeService);

    expect(service.applique()).toBe('clair');
    expect(themeAffiche()).toBe('clair');
  });
});
