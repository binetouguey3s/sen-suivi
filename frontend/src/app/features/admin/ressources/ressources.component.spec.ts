import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../../core/config/api.config';
import { AdministrationService } from '../../../core/services/administration.service';
import { AdminRessourcesComponent } from './ressources.component';

describe('AdminRessourcesComponent, fichier audio', () => {
  let fixture: ComponentFixture<AdminRessourcesComponent>;
  let hote: HTMLElement;
  let service: { creerRessource: ReturnType<typeof vi.fn>; modifierRessource: ReturnType<typeof vi.fn>; envoyerAudio: ReturnType<typeof vi.fn>; retirerAudio: ReturnType<typeof vi.fn>; supprimerRessource: ReturnType<typeof vi.fn> };

  const bouton = (texte: string): HTMLButtonElement =>
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent!.trim().startsWith(texte))!;

  function saisir(selecteur: string, valeur: string): void {
    const champ = hote.querySelector<HTMLInputElement | HTMLTextAreaElement>(selecteur)!;
    champ.value = valeur;
    champ.dispatchEvent(new Event('input'));
  }

  beforeEach(async () => {
    service = {
      creerRessource: vi.fn().mockResolvedValue({ id: 31 }),
      modifierRessource: vi.fn().mockResolvedValue(undefined),
      envoyerAudio: vi.fn(async (_id: number, _f: File, progression: (p: number) => void) => progression(100)),
      retirerAudio: vi.fn().mockResolvedValue(undefined),
      supprimerRessource: vi.fn(),
    };
    await TestBed.configureTestingModule({
      imports: [AdminRessourcesComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), { provide: AdministrationService, useValue: service }],
    }).compileComponents();
    fixture = TestBed.createComponent(AdminRessourcesComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
    TestBed.inject(HttpTestingController).match(`${API_BASE_URL}/ressources`).forEach((r) => r.flush([]));
    await fixture.whenStable();
    fixture.detectChanges();
  });

  // Laisse finir l'enregistrement, puis sert le rechargement de la liste
  async function terminer(): Promise<void> {
    for (let i = 0; i < 5; i++) await new Promise((r) => setTimeout(r));
    TestBed.inject(HttpTestingController).match(`${API_BASE_URL}/ressources`).forEach((r) => r.flush([]));
    fixture.detectChanges();
  }

  async function nouveauPodcast(): Promise<void> {
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => /Ajouter|Nouvelle/.test(b.textContent!))!.click();
    fixture.detectChanges();
    saisir('[role="dialog"] input[type="text"]', 'La teranga commence par soi-même');
    bouton('Podcast').click();
    fixture.detectChanges();
    const champs = hote.querySelectorAll<HTMLInputElement>('[role="dialog"] input[type="text"]');
    champs[1].value = 'Bien-être';
    champs[1].dispatchEvent(new Event('input'));
    saisir('[role="dialog"] textarea', 'Un épisode pour souffler.');
    fixture.detectChanges();
  }

  it('le champ audio n’apparaît que pour un podcast', async () => {
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => /Ajouter|Nouvelle/.test(b.textContent!))!.click();
    fixture.detectChanges();
    expect(hote.querySelector('ss-champ-audio')).toBeNull();
    bouton('Podcast').click();
    fixture.detectChanges();
    expect(hote.querySelector('ss-champ-audio')).not.toBeNull();
  });

  it('crée le podcast puis envoie le fichier choisi', async () => {
    await nouveauPodcast();
    const champ = hote.querySelector<HTMLInputElement>('ss-champ-audio input[type="file"]')!;
    const fichier = new File([new Uint8Array(8)], 'teranga.mp3', { type: 'audio/mpeg' });
    Object.defineProperty(champ, 'files', { value: [fichier] });
    champ.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    bouton('Enregistrer').click();
    await terminer();

    expect(service.creerRessource).toHaveBeenCalledWith(expect.objectContaining({ type_ressource: 'PODCAST' }));
    expect(service.envoyerAudio).toHaveBeenCalledWith(31, fichier, expect.any(Function));
  });

  it('sans fichier, rien n’est envoyé', async () => {
    await nouveauPodcast();
    bouton('Enregistrer').click();
    await terminer();

    expect(service.creerRessource).toHaveBeenCalled();
    expect(service.envoyerAudio).not.toHaveBeenCalled();
  });

  it('un envoi en échec garde la ressource et explique quoi faire', async () => {
    service.envoyerAudio.mockRejectedValue(new Error('413'));
    await nouveauPodcast();
    const champ = hote.querySelector<HTMLInputElement>('ss-champ-audio input[type="file"]')!;
    Object.defineProperty(champ, 'files', { value: [new File([new Uint8Array(8)], 'teranga.mp3')] });
    champ.dispatchEvent(new Event('change'));
    bouton('Enregistrer').click();
    await terminer();
    fixture.detectChanges();

    expect(hote.querySelector('[role="alert"]')!.textContent).toContain("le fichier audio n'a pas pu être envoyé");
  });
});
