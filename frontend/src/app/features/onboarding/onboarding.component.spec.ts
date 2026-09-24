import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { OnboardingComponent } from './onboarding.component';

// Accès aux membres protégés du composant, réservé aux tests
type Interne = { index: () => number; phase: () => string };

// jsdom n'a pas toujours PointerEvent : on fabrique un événement équivalent
function pointeur(type: string, x: number, y = 0): Event {
  const e = new MouseEvent(type, { clientX: x, clientY: y, bubbles: true });
  Object.defineProperties(e, { pointerId: { value: 1 }, pointerType: { value: 'touch' } });
  return e;
}

function simulerMouvementReduit(actif: boolean): void {
  vi.stubGlobal('matchMedia', (requete: string) => ({
    matches: actif && requete.includes('reduce'),
    media: requete,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
}

describe('OnboardingComponent', () => {
  let fixture: ComponentFixture<OnboardingComponent>;
  let hote: HTMLElement;

  const interne = (): Interne => fixture.componentInstance as unknown as Interne;
  const badge = (): string => hote.querySelector('.ob__badge')!.textContent!.trim();
  const carte = (): HTMLElement => hote.querySelector('.ob__carte')!;
  const boutonSuivant = (): HTMLButtonElement => hote.querySelector('.ob__suivant')!;

  function creer(): void {
    fixture = TestBed.createComponent(OnboardingComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
  }

  // Laisse passer toute la transition (sortie + entrée en cascade)
  function finirTransition(): void {
    vi.advanceTimersByTime(1000);
    fixture.detectChanges();
  }

  function balayer(dx: number): void {
    carte().dispatchEvent(pointeur('pointerdown', 300));
    carte().dispatchEvent(pointeur('pointermove', 300 + dx / 2));
    carte().dispatchEvent(pointeur('pointermove', 300 + dx));
    carte().dispatchEvent(pointeur('pointerup', 300 + dx));
  }

  function touche(key: string): void {
    document.dispatchEvent(new KeyboardEvent('keydown', { key }));
  }

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'requestAnimationFrame', 'cancelAnimationFrame', 'performance'] });
    simulerMouvementReduit(false);
    TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [provideRouter([])],
    });
  });

  afterEach(() => {
    fixture?.destroy();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("avance et recule d'étape en mettant à jour l'index et le badge", () => {
    creer();
    expect(badge()).toBe('Étape 1 sur 3');

    boutonSuivant().click();
    finirTransition();
    expect(interne().index()).toBe(1);
    expect(badge()).toBe('Étape 2 sur 3');

    touche('ArrowLeft');
    finirTransition();
    expect(interne().index()).toBe(0);
    expect(badge()).toBe('Étape 1 sur 3');

    touche('ArrowRight');
    finirTransition();
    expect(badge()).toBe('Étape 2 sur 3');
  });

  it('ignore un second déclenchement pendant la transition', () => {
    creer();
    boutonSuivant().click();
    boutonSuivant().click();
    finirTransition();
    expect(interne().index()).toBe(1);
  });

  it("annonce l'étape et place le focus sur le titre", () => {
    creer();
    boutonSuivant().click();
    finirTransition();
    expect(hote.querySelector('[aria-live="polite"]')!.textContent!.trim()).toBe('Étape 2 sur 3');
    expect(document.activeElement).toBe(hote.querySelector('h1'));
  });

  it("change d'étape avec un balayage supérieur au seuil", () => {
    creer();
    balayer(-100);
    finirTransition();
    expect(interne().index()).toBe(1);

    balayer(100);
    finirTransition();
    expect(interne().index()).toBe(0);
  });

  it('ne change rien avec un balayage inférieur au seuil', () => {
    creer();
    balayer(-40);
    finirTransition();
    expect(interne().index()).toBe(0);
    expect(badge()).toBe('Étape 1 sur 3');
  });

  it('« Passer » mène directement à la fin du parcours', () => {
    creer();
    const navigation = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    (hote.querySelector('.ob__passer') as HTMLButtonElement).click();
    expect(navigation).toHaveBeenCalledWith('/app');
  });

  it("avec .sans-animation, l'étape change immédiatement, sans phase de transition", () => {
    simulerMouvementReduit(true);
    creer();
    expect(hote.classList).toContain('sans-animation');
    expect(interne().phase()).toBe('repos');

    boutonSuivant().click();
    fixture.detectChanges();
    // Aucune minuterie avancée : le changement est instantané
    expect(interne().index()).toBe(1);
    expect(interne().phase()).toBe('repos');
    expect(carte().classList).not.toContain('ob--sortie');
    expect(carte().classList).not.toContain('ob--entree');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('retire les écouteurs et les minuteries à la destruction', () => {
    creer();
    const composant = interne();
    const elementCarte = carte();

    fixture.destroy();
    expect(vi.getTimerCount()).toBe(0);

    touche('ArrowRight');
    elementCarte.dispatchEvent(pointeur('pointerdown', 300));
    elementCarte.dispatchEvent(pointeur('pointermove', 150));
    elementCarte.dispatchEvent(pointeur('pointerup', 150));
    vi.advanceTimersByTime(1000);
    expect(composant.index()).toBe(0);
  });
});
