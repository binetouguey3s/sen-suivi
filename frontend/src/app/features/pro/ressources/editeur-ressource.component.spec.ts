import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../../core/config/api.config';
import { AuthService } from '../../../core/services/auth.service';
import { FavorisService } from '../../../core/services/favoris.service';
import { RessourcesProService } from '../../../core/services/ressources-pro.service';
import { EditeurRessourceComponent } from './editeur-ressource.component';

describe('EditeurRessourceComponent', () => {
  let fixture: ComponentFixture<EditeurRessourceComponent>;
  let hote: HTMLElement;
  let service: { creer: ReturnType<typeof vi.fn>; modifier: ReturnType<typeof vi.fn>; soumettre: ReturnType<typeof vi.fn>; envoyerAudio: ReturnType<typeof vi.fn> };

  const aide = () => hote.querySelector('#ed-aide-soumettre')!.textContent!.trim();
  const soumettre = () => hote.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  const bouton = (texte: string) => [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent!.trim().startsWith(texte))!;

  function saisir(selecteur: string, valeur: string): void {
    const champ = hote.querySelector<HTMLInputElement | HTMLTextAreaElement>(selecteur)!;
    champ.value = valeur;
    champ.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  function remplir(): void {
    saisir('#ed-titre', 'Trois respirations pour décrocher');
    bouton('Stress').click();
    fixture.detectChanges();
    saisir('#ed-texte', '## 1. Poser le sac\nArrêtez-vous une minute.');
  }

  function cocherCharte(): void {
    const charte = hote.querySelector<HTMLInputElement>('.ed__charte input')!;
    charte.checked = true;
    charte.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    service = {
      creer: vi.fn(async (d) => ({ id: 42, statut: 'BROUILLON', ...d })),
      modifier: vi.fn(async (id, d) => ({ id, statut: 'BROUILLON', ...d })),
      soumettre: vi.fn(async (id) => ({ id, statut: 'EN_ATTENTE' })),
      envoyerAudio: vi.fn(),
    };
    await TestBed.configureTestingModule({
      imports: [EditeurRessourceComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: { identifiant: () => 7, nom: () => 'Awa Ndiaye' } },
        { provide: RessourcesProService, useValue: service },
        { provide: FavorisService, useValue: { estFavori: () => false, basculer: vi.fn() } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(EditeurRessourceComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    http.expectOne(`${API_BASE_URL}/ressources`).flush([{ thematique: 'Stress' }, { thematique: 'Sommeil' }]);
    http.expectOne(`${API_BASE_URL}/professionnels/7`).flush({ nom: 'Awa Ndiaye', specialite_affichee: 'Sophrologue' });
    await fixture.whenStable();
    fixture.detectChanges();
  });

  afterEach(() => vi.useRealTimers());

  it('« Soumettre » reste désactivé et dit exactement ce qui manque', () => {
    expect(soumettre().disabled).toBe(true);
    expect(aide()).toBe('Ajoutez un titre (8 caractères au moins).');

    saisir('#ed-titre', 'Trois respirations pour décrocher');
    expect(aide()).toBe('Choisissez une thématique.');

    bouton('Stress').click();
    fixture.detectChanges();
    expect(aide()).toBe('Écrivez le contenu de la ressource.');

    saisir('#ed-texte', 'Arrêtez-vous une minute.');
    expect(aide()).toBe('Cochez l’engagement pour soumettre.');

    cocherCharte();
    expect(soumettre().disabled).toBe(false);
    expect(aide()).toBe('Prêt à être relu par l’équipe.');
  });

  it('une vidéo exige un lien YouTube valide, vérifié en direct', () => {
    bouton('Vidéo').click();
    fixture.detectChanges();
    remplir();
    cocherCharte();
    expect(aide()).toBe('Ajoutez un lien YouTube valide.');

    saisir('#ed-video', 'https://vimeo.com/123456');
    expect(hote.querySelector('.ed-etat--erreur')!.textContent).toContain('Seuls les liens YouTube sont acceptés.');
    expect(hote.querySelector('ss-video-youtube')).toBeNull();

    saisir('#ed-video', 'https://youtu.be/aXItOY0sLRY');
    expect(hote.querySelector('.ed-etat--ok')!.textContent).toContain('Vidéo reconnue');
    expect(hote.querySelector('ss-video-youtube')).not.toBeNull();
    expect(soumettre().disabled).toBe(false);
  });

  it('un podcast exige son fichier audio', () => {
    bouton('Podcast').click();
    fixture.detectChanges();
    remplir();
    cocherCharte();
    expect(aide()).toBe('Ajoutez votre fichier audio.');
    expect(hote.querySelector('.ed__depot')!.textContent).toContain('Glissez votre fichier ici');
  });

  it('l’aperçu de la carte se met à jour en direct, avec la signature', () => {
    expect(hote.querySelector('.ed__cote .cr__titre')!.textContent).toContain('Titre de votre ressource');
    saisir('#ed-titre', 'Mieux dormir quand on pense trop');
    saisir('#ed-chapo', 'Un exercice pour le soir.');

    const carte = hote.querySelector('.ed__cote ss-carte-ressource')!;
    expect(carte.querySelector('.cr__titre')!.textContent).toContain('Mieux dormir quand on pense trop');
    expect(carte.querySelector('.cr__chapo')!.textContent).toContain('Un exercice pour le soir.');
    expect(carte.querySelector('.cr__signature')!.textContent!.replace(/\s+/g, ' ')).toContain('Proposé par Awa Ndiaye, Sophrologue');
  });

  it('les raccourcis insèrent ##, > et - à la position du curseur', () => {
    saisir('#ed-texte', 'Premier paragraphe.');
    const champ = hote.querySelector<HTMLTextAreaElement>('#ed-texte')!;
    champ.selectionStart = champ.selectionEnd = champ.value.length;

    bouton('Intertitre').click();
    fixture.detectChanges();

    expect(champ.value).toBe('Premier paragraphe.\n## ');
    bouton('Citation').click();
    expect(champ.value).toBe('Premier paragraphe.\n## \n> ');
  });

  it('soumettre enregistre le brouillon puis l’envoie à l’équipe', async () => {
    const naviguer = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    remplir();
    cocherCharte();

    soumettre().click();
    await fixture.whenStable();

    expect(service.creer).toHaveBeenCalledWith(expect.objectContaining({ titre: 'Trois respirations pour décrocher', thematique: 'Stress' }));
    expect(service.soumettre).toHaveBeenCalledWith(42);
    expect(naviguer).toHaveBeenCalledWith('/pro/ressources');
  });

  it('quitter avec des modifications propose d’enregistrer le brouillon', async () => {
    saisir('#ed-titre', 'Un titre en cours');
    const reponse = fixture.componentInstance.peutQuitter() as Promise<boolean>;
    fixture.detectChanges();
    expect(hote.querySelector('[role="dialog"]')!.textContent).toContain('Enregistrer le brouillon avant de partir');

    bouton('Enregistrer et quitter').click();

    expect(await reponse).toBe(true);
    expect(service.creer).toHaveBeenCalled();
  });

  it('sans modification, on quitte directement', () => {
    expect(fixture.componentInstance.peutQuitter()).toBe(true);
  });

  it('le brouillon s’enregistre tout seul toutes les 20 secondes s’il a changé', async () => {
    vi.advanceTimersByTime(20_000);
    expect(service.creer).not.toHaveBeenCalled();
    saisir('#ed-titre', 'Un titre en cours');
    vi.advanceTimersByTime(20_000);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(service.creer).toHaveBeenCalledTimes(1);
    expect(hote.querySelector('.ed__sauve')!.textContent).toContain('Brouillon enregistré à');
  });
});
