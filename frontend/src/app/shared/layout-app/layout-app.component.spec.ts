import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../core/config/api.config';
import { AuthService } from '../../core/services/auth.service';
import { ConversationService } from '../../core/services/conversation.service';
import { RessourcesProService } from '../../core/services/ressources-pro.service';
import { ClocheNotificationsComponent } from '../panneau-notifications/panneau-notifications.component';
import { LayoutAppComponent } from './layout-app.component';

// La cloche a ses propres tests : ici, seule la navigation compte
@Component({ selector: 'ss-cloche-notifications', standalone: true, template: '' })
class ClocheVide {}

async function afficherPro() {
  await TestBed.configureTestingModule({
    imports: [LayoutAppComponent],
    providers: [
      provideRouter([]),
      provideHttpClient(),
      provideHttpClientTesting(),
      {
        provide: AuthService,
        useValue: { typeCompte: () => 'professionnel', identifiant: () => 7, nom: () => 'Awa Ndiaye', prenom: () => null, deconnecter: vi.fn() },
      },
      { provide: ConversationService, useValue: { ouverte: signal(false), basculer: vi.fn() } },
    ],
  })
    .overrideComponent(LayoutAppComponent, { remove: { imports: [ClocheNotificationsComponent] }, add: { imports: [ClocheVide] } })
    .compileComponents();
  const fixture = TestBed.createComponent(LayoutAppComponent);
  fixture.detectChanges();
  const http = TestBed.inject(HttpTestingController);
  http.match(`${API_BASE_URL}/professionnels/7`).forEach((r) => r.flush({ nom: 'Awa Ndiaye', specialite_affichee: 'Sophrologue' }));
  return { fixture, http, hote: fixture.nativeElement as HTMLElement };
}

const lienRessources = (hote: HTMLElement) =>
  [...hote.querySelectorAll<HTMLAnchorElement>('.layout-app__lien')].find((a) => a.textContent!.includes('Mes ressources'))!;

describe('LayoutAppComponent, navigation du professionnel', () => {
  it('« Mes ressources » se place entre Disponibilités et Paramètres, avec le nombre en attente', async () => {
    const { fixture, http, hote } = await afficherPro();
    http.expectOne(`${API_BASE_URL}/pro/ressources`).flush([{ statut: 'EN_ATTENTE' }, { statut: 'EN_ATTENTE' }, { statut: 'PUBLIEE' }]);
    await fixture.whenStable();
    fixture.detectChanges();

    const libelles = [...hote.querySelectorAll('.layout-app__lien')].map((a) => a.textContent!.replace(/\s+/g, ' ').trim());
    expect(libelles.findIndex((l) => l.startsWith('Mes ressources'))).toBe(libelles.findIndex((l) => l.startsWith('Disponibilités')) + 1);
    expect(lienRessources(hote).querySelector('.layout-app__compteur')!.textContent!.trim()).toBe('2');
  });

  it('aucune pastille quand rien n’est en attente, et le compteur suit les changements', async () => {
    const { fixture, http, hote } = await afficherPro();
    http.expectOne(`${API_BASE_URL}/pro/ressources`).flush([{ statut: 'BROUILLON' }]);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(lienRessources(hote).querySelector('.layout-app__compteur')).toBeNull();

    // Une soumission incrémente la version : la liste est relue
    TestBed.inject(RessourcesProService).version.update((v) => v + 1);
    fixture.detectChanges();
    http.expectOne(`${API_BASE_URL}/pro/ressources`).flush([{ statut: 'EN_ATTENTE' }]);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(lienRessources(hote).querySelector('.layout-app__compteur')!.textContent!.trim()).toBe('1');
  });
});
