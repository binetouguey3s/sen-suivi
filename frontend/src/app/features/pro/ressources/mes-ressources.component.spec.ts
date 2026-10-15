import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../../core/config/api.config';
import { Ressource } from '../../../core/models/suivi';
import { AuthService } from '../../../core/services/auth.service';
import { RessourcesProService } from '../../../core/services/ressources-pro.service';
import { MesRessourcesComponent } from './mes-ressources.component';

function ressource(id: number, statut: Ressource['statut'], extra: Partial<Ressource> = {}): Ressource {
  return {
    id, statut, titre: `Ressource numéro ${id}`, type_ressource: 'EXERCICE', thematique: 'Stress', contenu: 'Chapô.',
    duree_lecture: 4, date_publication: '2026-10-02', date_modification: '2026-10-14T10:00:00Z', date_soumission: '2026-10-13T10:00:00Z',
    ...extra,
  };
}

const RESSOURCES = [
  ressource(1, 'PUBLIEE'),
  ressource(2, 'PUBLIEE', { type_ressource: 'VIDEO' }),
  ressource(3, 'EN_ATTENTE'),
  ressource(4, 'REFUSEE', { motif_refus: 'Retirez le nom du médicament au paragraphe 3.' }),
  ressource(5, 'BROUILLON'),
];

describe('MesRessourcesComponent', () => {
  let fixture: ComponentFixture<MesRessourcesComponent>;
  let hote: HTMLElement;
  let service: RessourcesProService;

  const ligne = (id: number): HTMLElement =>
    [...hote.querySelectorAll<HTMLElement>('.mr__ligne')].find((l) => l.textContent!.includes(`Ressource numéro ${id}`))!;
  const actions = (id: number) => [...ligne(id).querySelectorAll('.mr__actions a, .mr__actions button')].map((e) => e.textContent!.trim());

  async function afficher(liste: Ressource[] = RESSOURCES): Promise<void> {
    fixture = TestBed.createComponent(MesRessourcesComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    http.expectOne(`${API_BASE_URL}/pro/ressources`).flush(liste);
    http.expectOne(`${API_BASE_URL}/professionnels/7`).flush({ nom: 'Awa Ndiaye', specialite_affichee: 'Sophrologue', ville: 'Dakar' });
    await fixture.whenStable();
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MesRessourcesComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: { identifiant: () => 7, nom: () => 'Awa Ndiaye' } },
      ],
    }).compileComponents();
    service = TestBed.inject(RessourcesProService);
  });

  it('montre la signature réelle et le résumé chiffré', async () => {
    await afficher();
    expect(hote.querySelector('.mr__auteur')!.textContent).toContain('« Proposé par Awa Ndiaye, Sophrologue »');
    const resume = [...hote.querySelectorAll('.mr__resume > span')].map((s) => s.textContent!.replace(/\s+/g, ' ').trim());
    expect(resume).toEqual(['2publiées', '1en attente', '1à corriger']);
    expect(hote.textContent).not.toContain('lectures');
  });

  it('filtre par onglet de statut', async () => {
    await afficher();
    const onglets = [...hote.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
    expect(onglets.map((o) => o.textContent!.replace(/\s+/g, ' ').trim())).toEqual([
      'Toutes 5', 'Publiées 2', 'En attente 1', 'Brouillons 1', 'À corriger 1',
    ]);

    onglets[1].click();
    fixture.detectChanges();

    expect(hote.querySelectorAll('.mr__ligne')).toHaveLength(2);
    expect(onglets[1].getAttribute('aria-selected')).toBe('true');
  });

  it('propose les actions selon le statut', async () => {
    await afficher();
    expect(actions(1)).toEqual(['Voir', 'Copier le lien']);
    expect(actions(3)).toEqual(['Aperçu']);
    expect(actions(5)).toEqual(['Continuer', 'Supprimer']);
    expect(actions(4)).toEqual(['Corriger', 'Supprimer']);
    expect(ligne(4).querySelector('.mr__motif')!.textContent).toContain('Retirez le nom du médicament');
    expect(ligne(3).textContent).toContain('Soumise le 13 oct. 2026');
  });

  it('supprime après confirmation dans la modale', async () => {
    const supprimer = vi.spyOn(service, 'supprimer').mockResolvedValue();
    await afficher();
    [...ligne(5).querySelectorAll('button')].find((b) => b.textContent!.includes('Supprimer'))!.click();
    fixture.detectChanges();
    expect(hote.querySelector('[role="dialog"]')!.textContent).toContain('Ressource numéro 5');

    [...hote.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')].find((b) => b.textContent!.trim() === 'Supprimer')!.click();
    await fixture.whenStable();

    expect(supprimer).toHaveBeenCalledWith(5);
  });

  it('affiche le message après une soumission réussie', async () => {
    service.soumissionReussie.set(true);
    await afficher();
    expect(hote.querySelector('.mr__toast')!.textContent).toContain('Ressource envoyée à l’équipe Sen Suivi.');
  });

  it('liste vide : invite à proposer une première ressource', async () => {
    await afficher([]);
    expect(hote.textContent).toContain('Vous n’avez pas encore proposé de ressource');
    expect(hote.textContent).toContain('Proposer ma première ressource');
  });
});
