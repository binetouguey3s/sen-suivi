import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Compte, CompteService } from '../../core/services/compte.service';
import { ConversationService } from '../../core/services/conversation.service';
import { OnboardingComponent } from './onboarding.component';
import { OnboardingStore } from './onboarding.store';

const COMPTE: Compte = {
  id: 1,
  type_compte: 'utilisateur',
  nom: 'Diop',
  prenom: 'Awa',
  email: 'awa@exemple.sn',
  ville: 'Dakar',
  pseudonyme: 'Jamm',
  preferences: { nouvelle_demande: { email: false } },
};

describe('OnboardingComponent', () => {
  let fixture: ComponentFixture<OnboardingComponent>;
  let hote: HTMLElement;
  let modifier: ReturnType<typeof vi.fn>;
  let definirConservation: ReturnType<typeof vi.fn>;

  const titre = (): string => hote.querySelector('h1')!.textContent!.replace(/\s+/g, ' ').trim();
  const suivant = (): HTMLButtonElement => hote.querySelector('.ob__suivant')!;
  const bouton = (texte: string): HTMLButtonElement =>
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent!.trim() === texte)!;

  async function cliquer(el: HTMLElement): Promise<void> {
    el.click();
    fixture.detectChanges();
    // Laisse se terminer l'enregistrement (promesses) avant de relire l'écran
    await new Promise((r) => setTimeout(r));
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function allerA(nombre: number): Promise<void> {
    for (let i = 0; i < nombre; i++) await cliquer(suivant());
  }

  beforeEach(async () => {
    modifier = vi.fn(async (d: Partial<Compte>) => ({ ...COMPTE, ...d }));
    definirConservation = vi.fn(async () => undefined);
    await TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [
        provideRouter([]),
        {
          provide: CompteService,
          useValue: { compte: () => COMPTE, charger: async () => COMPTE, modifier },
        },
        { provide: ConversationService, useValue: { definirConservation, consentementConservation: () => false } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(OnboardingComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
  });

  it("commence par l'écran d'accueil, sans barre de progression", () => {
    expect(titre()).toBe('Un esprit sain pour une société saine');
    expect(hote.querySelector('[role="progressbar"]')).toBeNull();
  });

  it('salue la personne par son prénom sur la présentation', async () => {
    await allerA(1);
    expect(titre()).toBe('Faisons connaissance');
    expect(hote.querySelector('.ob__bulle')!.textContent).toContain('Bonjour Awa');
  });

  it('affiche la progression pendant les six étapes', async () => {
    await allerA(2);
    expect(titre()).toContain('Parlez-nous un peu de vous');
    expect(hote.querySelector('[role="progressbar"]')!.getAttribute('aria-valuenow')).toBe('1');
    await allerA(1);
    expect(hote.querySelector('[role="progressbar"]')!.getAttribute('aria-valuenow')).toBe('2');
  });

  it('limite les préoccupations à trois sujets', async () => {
    await allerA(4);
    for (const s of ['Stress', 'Travail', 'Sommeil']) await cliquer(bouton(s));
    expect(bouton('Famille').disabled).toBe(true);
    expect(hote.textContent).toContain('Vous avez atteint le maximum');
  });

  it('ouvre le choix spirituel quand on sélectionne « Spiritualité et prière »', async () => {
    await allerA(5);
    await cliquer(bouton('Spiritualité et prière'));
    expect(hote.querySelector('[role="dialog"]')).not.toBeNull();
  });

  it('enregistre les réponses à la fin, sans effacer les autres préférences', async () => {
    await allerA(2);
    await cliquer(bouton('Une femme'));
    await allerA(5);
    expect(suivant().textContent).toContain('Créer mon parcours');
    await cliquer(suivant());

    expect(modifier).toHaveBeenCalledTimes(1);
    const { preferences } = modifier.mock.calls[0][0];
    expect(preferences.nouvelle_demande).toEqual({ email: false });
    expect(preferences.onboarding.statut).toBe('termine');
    expect(preferences.onboarding.genre).toBe('femme');
    expect(preferences.personnalisation_chatbot).toBe(false);
    expect(definirConservation).not.toHaveBeenCalled();
    expect(titre()).toContain('Votre parcours est prêt, Awa');
  });

  it('« Passer » garde les réponses déjà données puis ouvre l’espace', async () => {
    const naviguer = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    await allerA(2);
    await cliquer(bouton('Passer'));
    expect(modifier.mock.calls[0][0].preferences.onboarding.statut).toBe('passe');
    expect(naviguer).toHaveBeenCalledWith('/app');
  });
});

describe('OnboardingComponent, questionnaire refait', () => {
  it('repart des réponses déjà enregistrées', async () => {
    const compte: Compte = {
      ...COMPTE,
      preferences: {
        personnalisation_chatbot: true,
        onboarding: {
          version: 1,
          statut: 'termine',
          date: '2026-10-01T10:00:00Z',
          genre: 'femme',
          preoccupations: ['stress', 'etudes'],
          rien_de_particulier: false,
          bien_etre: ['musique'],
          spiritualite: [],
          moments: [],
          formats: [],
          rappels: false,
          metiers: [],
        },
      },
    };
    await TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [
        provideRouter([]),
        { provide: CompteService, useValue: { compte: () => compte, charger: async () => compte, modifier: vi.fn() } },
        { provide: ConversationService, useValue: { definirConservation: vi.fn(), consentementConservation: () => false } },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(OnboardingComponent);
    const store = fixture.debugElement.injector.get(OnboardingStore);

    expect(store.genre()).toBe('femme');
    expect(store.preoccupations()).toEqual(['stress', 'etudes']);
    expect(store.bienEtre()).toEqual(['musique']);
    expect(store.rappels()).toBe(false);
    expect(store.personnalisation()).toBe(true);
  });
});
