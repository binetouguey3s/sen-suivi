import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../core/config/api.config';
import { AuthService } from '../../core/services/auth.service';
import { Compte, CompteService, Preferences } from '../../core/services/compte.service';
import { SuiviHumeurService } from '../../core/services/suivi-humeur.service';
import { TableauDeBordComponent } from './tableau-de-bord.component';

const RESSOURCES = [
  { id: 1, titre: 'Comprendre le stress', type_ressource: 'ARTICLE', thematique: 'Stress', contenu: '…', duree_lecture: 6, date_publication: '2026-09-01' },
  { id: 2, titre: 'Dormir mieux', type_ressource: 'PODCAST', thematique: 'Sommeil', contenu: '…', duree_lecture: 12, date_publication: '2026-09-03' },
  { id: 3, titre: 'Parler en famille', type_ressource: 'ARTICLE', thematique: 'Famille', contenu: '…', duree_lecture: 7, date_publication: '2026-10-10' },
  { id: 4, titre: 'Pauses au travail', type_ressource: 'ARTICLE', thematique: 'Travail', contenu: '…', duree_lecture: 5, date_publication: '2026-10-12' },
];

async function afficher(preferences: Preferences) {
  const compte = signal<Compte | null>({
    id: 1, type_compte: 'utilisateur', nom: 'Diop', prenom: 'Awa', email: 'awa@exemple.sn', ville: null, pseudonyme: 'Jamm', preferences,
  });
  await TestBed.configureTestingModule({
    imports: [TableauDeBordComponent],
    providers: [
      provideRouter([]),
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: AuthService, useValue: { prenom: () => 'Awa', nom: () => 'Diop' } },
      { provide: CompteService, useValue: { compte, charger: vi.fn() } },
      { provide: SuiviHumeurService, useValue: { publier: vi.fn() } },
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(TableauDeBordComponent);
  fixture.detectChanges();
  const http = TestBed.inject(HttpTestingController);
  http.expectOne(`${API_BASE_URL}/suivi-humeur?periode=30j`).flush([]);
  http.expectOne(`${API_BASE_URL}/ressources`).flush(RESSOURCES);
  http.expectOne(`${API_BASE_URL}/lieux`).flush([]);
  await fixture.whenStable();
  fixture.detectChanges();
  const hote: HTMLElement = fixture.nativeElement;
  const cartes = [...hote.querySelectorAll<HTMLAnchorElement>('.tdb__suggestion')];
  return { hote, cartes, fixture };
}

describe('TableauDeBordComponent, « Pour vous »', () => {
  it('affiche 3 cartes avec thème, titre, durée, raison et lien', async () => {
    const { hote, cartes } = await afficher({
      personnalisation_chatbot: true,
      onboarding: {
        version: 1, statut: 'termine', date: '2026-10-01', preoccupations: ['sommeil', 'stress'], rien_de_particulier: false,
        bien_etre: [], spiritualite: [], moments: [], formats: [], rappels: true, metiers: [],
      },
    });

    expect(hote.querySelector('#tdb-pour-vous')!.textContent).toContain('Pour vous');
    expect(cartes).toHaveLength(3);
    const premiere = cartes[0].textContent!.replace(/\s+/g, ' ');
    expect(premiere).toContain('Sommeil');
    expect(premiere).toContain('Dormir mieux');
    expect(premiere).toContain('12 min');
    expect(premiere).toContain('Parce que vous avez choisi : Sommeil');
    expect(cartes[0].getAttribute('href')).toBe('/ressources/2');
    // Profil et consentement présents : rien à personnaliser
    expect(hote.querySelector('a[href="/app/profil"]')).toBeNull();
  });

  it('sans consentement : les nouveautés, et un lien pour personnaliser', async () => {
    const { hote, cartes } = await afficher({});

    expect(cartes.map((c) => c.getAttribute('href'))).toEqual(['/ressources/4', '/ressources/3', '/ressources/2']);
    expect(cartes[0].textContent).toContain('Nouveauté');
    expect(hote.querySelector('a[href="/app/profil"]')!.textContent).toContain('Personnaliser');
  });

  it('affiche le conseil du jour, et « Un autre conseil » passe au suivant', async () => {
    const { hote, fixture } = await afficher({});
    const texte = () => hote.querySelector('.tdb__conseil p')!.textContent!.trim();
    const avant = texte();
    expect(avant.length).toBeGreaterThan(20);

    hote.querySelector<HTMLButtonElement>('.tdb__conseil-suivant')!.click();
    fixture.detectChanges();

    expect(texte()).not.toBe(avant);
  });
});
