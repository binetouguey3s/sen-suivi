import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SelecteurThemeComponent } from './selecteur-theme.component';

describe('SelecteurThemeComponent', () => {
  let fixture: ComponentFixture<SelecteurThemeComponent>;
  let hote: HTMLElement;

  const groupe = (): HTMLElement => hote.querySelector('[role="radiogroup"]')!;
  const options = (): HTMLButtonElement[] => [...hote.querySelectorAll<HTMLButtonElement>('[role="radio"]')];
  const cochee = (): HTMLButtonElement => options().find((b) => b.getAttribute('aria-checked') === 'true')!;
  const nom = (b: Element): string => b.textContent!.trim();

  function creer(compact = false): void {
    fixture = TestBed.createComponent(SelecteurThemeComponent);
    fixture.componentRef.setInput('compact', compact);
    hote = fixture.nativeElement;
    document.body.appendChild(hote);
    fixture.detectChanges();
  }

  // Touche envoyée à l'option qui a le focus, comme au clavier
  function touche(key: string): KeyboardEvent {
    const evenement = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
    (document.activeElement as HTMLElement).dispatchEvent(evenement);
    fixture.detectChanges();
    return evenement;
  }

  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: () => undefined, removeEventListener: () => undefined }));
    TestBed.resetTestingModule();
  });

  afterEach(() => {
    hote?.remove();
    vi.unstubAllGlobals();
  });

  describe('attributs ARIA', () => {
    it('forme un groupe radio nommé, avec trois options', () => {
      creer();
      expect(groupe().getAttribute('aria-label')).toBe("Thème d'affichage");
      expect(options().map(nom)).toEqual(['Clair', 'Sombre', 'Système']);
      options().forEach((b) => expect(b.getAttribute('type')).toBe('button'));
    });

    it('coche une seule option, celle du thème choisi', () => {
      creer();
      expect(options().map((b) => b.getAttribute('aria-checked'))).toEqual(['false', 'false', 'true']);
      expect(nom(cochee())).toBe('Système');
    });

    it('ne laisse qu’un seul arrêt de tabulation, sur l’option cochée', () => {
      creer();
      expect(options().map((b) => b.getAttribute('tabindex'))).toEqual(['-1', '-1', '0']);
    });

    it('garde des libellés explicites en version compacte (icônes seules)', () => {
      creer(true);
      expect(options().map(nom)).toEqual(['Thème clair', 'Thème sombre', "Thème de l'appareil"]);
      expect(options().map((b) => b.getAttribute('title'))).toEqual(['Thème clair', 'Thème sombre', "Thème de l'appareil"]);
    });
  });

  describe('clic', () => {
    it('coche l’option et applique le thème', () => {
      creer();
      options()[1].click();
      fixture.detectChanges();

      expect(nom(cochee())).toBe('Sombre');
      expect(document.documentElement.dataset['theme']).toBe('sombre');
      expect(options().map((b) => b.getAttribute('tabindex'))).toEqual(['-1', '0', '-1']);
    });
  });

  describe('clavier', () => {
    beforeEach(() => {
      creer();
      cochee().focus();
    });

    it('flèche droite et bas : option suivante, en boucle', () => {
      touche('ArrowRight');
      expect(nom(cochee())).toBe('Clair');
      expect(document.activeElement).toBe(cochee());

      touche('ArrowDown');
      expect(nom(cochee())).toBe('Sombre');
      expect(document.activeElement).toBe(cochee());
    });

    it('flèche gauche et haut : option précédente, en boucle', () => {
      touche('ArrowLeft');
      expect(nom(cochee())).toBe('Sombre');

      touche('ArrowUp');
      expect(nom(cochee())).toBe('Clair');

      touche('ArrowUp');
      expect(nom(cochee())).toBe('Système');
      expect(document.activeElement).toBe(cochee());
    });

    it('Début et Fin : première et dernière option', () => {
      touche('Home');
      expect(nom(cochee())).toBe('Clair');
      touche('End');
      expect(nom(cochee())).toBe('Système');
    });

    it('empêche le défilement de la page par les flèches', () => {
      expect(touche('ArrowDown').defaultPrevented).toBe(true);
    });

    it('laisse passer les autres touches (Tab, lettres)', () => {
      expect(touche('Tab').defaultPrevented).toBe(false);
      expect(touche('a').defaultPrevented).toBe(false);
      expect(nom(cochee())).toBe('Système');
    });
  });
});
