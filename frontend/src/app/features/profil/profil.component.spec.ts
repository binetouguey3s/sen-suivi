import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfilOnboarding } from '../../core/models/onboarding';
import { Compte, CompteService } from '../../core/services/compte.service';
import { ConversationService } from '../../core/services/conversation.service';
import { ProfilComponent } from './profil.component';

const ONBOARDING: ProfilOnboarding = {
  version: 1,
  statut: 'termine',
  date: '2026-10-01T10:00:00Z',
  genre: 'femme',
  tranche_age: '18-24',
  situation: 'etudiant',
  langue: 'fr',
  humeur: 4,
  energie: 60,
  preoccupations: ['stress', 'etudes'],
  rien_de_particulier: false,
  bien_etre: ['musique', 'spiritualite'],
  spiritualite: ['coran', 'dhikr'],
  moments: ['matin', 'soir'],
  duree: '5-10',
  formats: ['audio', 'exercice'],
  rappels: true,
  frequence_rappels: '3_semaine',
  metiers: [],
};

function compteAvec(preferences: Compte['preferences']): Compte {
  return {
    id: 1,
    type_compte: 'utilisateur',
    nom: 'Diop',
    prenom: 'Awa',
    email: 'awa@exemple.sn',
    ville: 'Dakar',
    pseudonyme: 'Jamm_rekk',
    preferences,
  };
}

describe('ProfilComponent', () => {
  let fixture: ComponentFixture<ProfilComponent>;
  let hote: HTMLElement;
  let modifier: ReturnType<typeof vi.fn>;

  const texte = (): string => hote.textContent!.replace(/\s+/g, ' ');
  const bouton = (libelle: string): HTMLButtonElement =>
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent!.trim() === libelle)!;
  const carte = (titre: string): HTMLElement =>
    [...hote.querySelectorAll<HTMLElement>('.pr-carte')].find((c) => c.querySelector('h3')?.textContent?.includes(titre))!;

  async function stabiliser(): Promise<void> {
    fixture.detectChanges();
    await new Promise((r) => setTimeout(r));
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function creer(preferences: Compte['preferences']): Promise<void> {
    const compte = signal<Compte | null>(compteAvec(preferences));
    modifier = vi.fn(async (d: Partial<Compte>) => {
      const nouveau = { ...compte()!, ...d } as Compte;
      compte.set(nouveau);
      return nouveau;
    });
    await TestBed.configureTestingModule({
      imports: [ProfilComponent],
      providers: [
        provideRouter([]),
        { provide: CompteService, useValue: { compte, charger: async () => compte()!, modifier } },
        {
          provide: ConversationService,
          useValue: {
            consentementConservation: () => false,
            erreurConservation: () => false,
            definirConservation: vi.fn(async () => undefined),
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ProfilComponent);
    hote = fixture.nativeElement;
    await stabiliser();
  }

  describe('avec un onboarding terminé', () => {
    beforeEach(() => creer({ nouvelle_demande: { email: false }, personnalisation_chatbot: true, onboarding: ONBOARDING }));

    it('affiche le prénom, le pseudonyme et la ville', () => {
      expect(hote.querySelector('h1')!.textContent).toContain('Awa');
      expect(texte()).toContain('@Jamm_rekk · visible sur le forum');
      expect(texte()).toContain('Dakar');
    });

    it('affiche les libellés, jamais les codes', () => {
      expect(carte('À propos de moi').textContent).toContain('Étudiant·e');
      expect(carte('À propos de moi').textContent).toContain('18–24 ans');
      expect(carte('À propos de moi').textContent).not.toContain('etudiant');
      expect(carte('Ce qui m’occupe l’esprit').textContent).toContain('Études et examens');
      expect(carte('Ce qui me fait du bien').textContent).toContain('Spiritualité : Récitation du Coran, Dhikr et invocations');
      expect(carte('Mon rythme').textContent).toContain('5–10 min par jour · Audio, Exercice guidé');
      expect(carte('Mon rythme').textContent).toContain('Rappels 3× / semaine');
    });

    it('propose « Ajouter » et « Non renseigné » pour une section vide', () => {
      const accompagnement = carte('Accompagnement');
      expect(accompagnement.textContent).toContain('Non renseigné');
      expect(accompagnement.querySelector('.pr-lien')!.textContent!.trim()).toBe('Ajouter');
      expect(texte()).toContain('Votre profil est complété à 80 %');
    });

    it('n’affiche ni l’humeur ni l’énergie, mais renvoie au journal', () => {
      expect(texte()).not.toContain('Énergie');
      expect(hote.querySelector('a.pr-journal')!.getAttribute('href')).toBe('/app/journal');
    });

    it('enregistre une section en fusionnant les préférences', async () => {
      carte('Ce qui m’occupe l’esprit').querySelector<HTMLButtonElement>('.pr-lien')!.click();
      await stabiliser();
      expect(hote.querySelector('[role="dialog"] h1')!.textContent).toContain('Qu’est-ce qui occupe votre esprit');

      bouton('Sommeil').click();
      await stabiliser();
      bouton('Enregistrer').click();
      await stabiliser();

      expect(modifier).toHaveBeenCalledTimes(1);
      const { preferences } = modifier.mock.calls[0][0];
      expect(preferences.nouvelle_demande).toEqual({ email: false });
      expect(preferences.personnalisation_chatbot).toBe(true);
      expect(preferences.onboarding.preoccupations).toEqual(['stress', 'etudes', 'sommeil']);
      expect(preferences.onboarding.genre).toBe('femme');
      expect(hote.querySelector('[role="dialog"]')).toBeNull();
      expect(carte('Ce qui m’occupe l’esprit').textContent).toContain('Sommeil');
    });

    it('modifier le rythme met à jour moments et fréquence, sans toucher au reste', async () => {
      carte('Mon rythme').querySelector<HTMLButtonElement>('.pr-lien')!.click();
      await stabiliser();
      bouton('À midi').click();
      bouton('Chaque jour').click();
      await stabiliser();
      bouton('Enregistrer').click();
      await stabiliser();

      const { preferences } = modifier.mock.calls[0][0];
      expect(preferences.onboarding.moments).toEqual(['matin', 'soir', 'midi']);
      expect(preferences.onboarding.rappels).toBe(true);
      expect(preferences.onboarding.frequence_rappels).toBe('quotidien');
      expect(preferences.onboarding.preoccupations).toEqual(['stress', 'etudes']);
      expect(preferences.nouvelle_demande).toEqual({ email: false });
      expect(preferences.personnalisation_chatbot).toBe(true);
      expect(carte('Mon rythme').textContent).toContain('Rappels chaque jour');
    });

    it('couper les rappels est enregistré dans l’onboarding', async () => {
      carte('Mon rythme').querySelector<HTMLButtonElement>('.pr-lien')!.click();
      await stabiliser();
      hote.querySelector<HTMLButtonElement>('[role="dialog"] [role="switch"][aria-label="Recevoir des rappels"]')!.click();
      await stabiliser();
      bouton('Enregistrer').click();
      await stabiliser();

      const { preferences } = modifier.mock.calls[0][0];
      expect(preferences.onboarding.rappels).toBe(false);
      expect(preferences.onboarding.frequence_rappels).toBeUndefined();
      expect(preferences.nouvelle_demande).toEqual({ email: false });
      expect(carte('Mon rythme').textContent).toContain('Rappels désactivés');
    });

    it('« Annuler » ne garde rien de la modification', async () => {
      carte('Ce qui m’occupe l’esprit').querySelector<HTMLButtonElement>('.pr-lien')!.click();
      await stabiliser();
      bouton('Sommeil').click();
      bouton('Annuler').click();
      await stabiliser();

      expect(modifier).not.toHaveBeenCalled();
      expect(carte('Ce qui m’occupe l’esprit').textContent).not.toContain('Sommeil');
    });

    it('« Effacer mes réponses » garde les autres préférences', async () => {
      bouton('Effacer mes réponses').click();
      await stabiliser();
      expect(texte()).toContain('Votre compte, votre journal et vos échanges ne sont pas touchés');

      bouton('Effacer').click();
      await stabiliser();

      const { preferences } = modifier.mock.calls[0][0];
      expect(preferences.onboarding).toBeUndefined();
      expect(preferences.nouvelle_demande).toEqual({ email: false });
      expect(preferences.personnalisation_chatbot).toBe(true);
      expect(texte()).toContain('Faites connaissance avec Titou en 2 minutes');
    });

    it('enregistre le consentement de personnalisation sans toucher au reste', async () => {
      hote.querySelector<HTMLButtonElement>('[role="switch"][aria-label="Personnaliser mes suggestions"]')!.click();
      await stabiliser();

      const { preferences } = modifier.mock.calls[0][0];
      expect(preferences.personnalisation_chatbot).toBe(false);
      expect(preferences.onboarding).toEqual(ONBOARDING);
      expect(texte()).toContain('Enregistré');
    });
  });

  describe('sans onboarding', () => {
    it('affiche l’état vide quand le questionnaire n’a pas été fait', async () => {
      await creer({});
      expect(texte()).toContain('Faites connaissance avec Titou en 2 minutes');
      expect(hote.querySelector('a.pr-bouton')!.getAttribute('href')).toBe('/bienvenue');
      expect(hote.querySelector('.pr-grille')).toBeNull();
    });

    it('affiche l’état vide quand le questionnaire a été passé', async () => {
      await creer({ onboarding: { ...ONBOARDING, statut: 'passe' } });
      expect(texte()).toContain('Faites connaissance avec Titou en 2 minutes');
    });
  });
});
