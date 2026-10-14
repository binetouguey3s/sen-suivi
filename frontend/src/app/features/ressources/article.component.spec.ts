import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../core/config/api.config';
import { FavorisService } from '../../core/services/favoris.service';
import { ArticleComponent } from './article.component';

const RESSOURCE = {
  id: 12,
  titre: 'Quand tout s’accumule : organiser sa semaine',
  type_ressource: 'EXERCICE',
  thematique: 'Organisation',
  contenu: 'Travail, famille, études : tout arrive en même temps.',
  duree_lecture: 10,
  date_publication: '2026-10-01T10:00:00Z',
};

describe('ArticleComponent, partage', () => {
  let fixture: ComponentFixture<ArticleComponent>;
  let hote: HTMLElement;
  let adresseAvant: string;

  beforeEach(async () => {
    adresseAvant = window.location.href;
    await TestBed.configureTestingModule({
      imports: [ArticleComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: FavorisService, useValue: { estFavori: () => false, basculer: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ArticleComponent);
    fixture.componentRef.setInput('id', '12');
    hote = fixture.nativeElement;
    document.body.appendChild(hote);
    fixture.detectChanges();

    const http = TestBed.inject(HttpTestingController);
    http.expectOne(`${API_BASE_URL}/ressources/12`).flush(RESSOURCE);
    http.match(`${API_BASE_URL}/ressources`).forEach((r) => r.flush([RESSOURCE]));
    await fixture.whenStable();
    fixture.detectChanges();
  });

  afterEach(() => {
    hote.remove();
    history.replaceState(null, '', adresseAvant);
  });

  it('copie l’adresse propre de la ressource, sans paramètres ni ancre', async () => {
    history.replaceState(null, '', '/ressources/12?depuis=accueil#2-les-trois-colonnes');
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });

    hote.querySelector<HTMLButtonElement>('button[aria-label="Partager"]')!.click();
    fixture.detectChanges();
    await fixture.whenStable();
    [...hote.querySelectorAll<HTMLElement>('[role="menuitem"]')].find((e) => e.textContent!.includes('Copier'))!.click();
    await fixture.whenStable();

    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/ressources/12`);
  });

  it('prévoit le bas de page du PDF avec l’adresse et le rappel d’urgence', () => {
    const pied = hote.querySelector('.art__pied-impression')!.textContent!.replace(/\s+/g, ' ');
    expect(pied).toContain(`Ressource Sen Suivi — ${window.location.origin}/ressources/12`);
    expect(pied).toContain('Sen Suivi ne remplace pas un professionnel de santé');
    expect(pied).toContain('SAMU 1515');
  });
});
