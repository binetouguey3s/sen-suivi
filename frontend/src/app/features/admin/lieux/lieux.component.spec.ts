import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../../core/config/api.config';
import { LieuDetente } from '../../../core/models/suivi';
import { AdministrationService } from '../../../core/services/administration.service';
import { AdminLieuxComponent } from './lieux.component';

vi.setConfig({ testTimeout: 30000 });

function lieu(id: number, nom: string, champs: Partial<LieuDetente> = {}): LieuDetente {
  return {
    id, nom, region: 'Kédougou', ville: 'Dindéfélo', type_lieu: '', description: '', categorie: 'Cascades & montagnes',
    latitude: null, longitude: null, acces: 'PAYANT', acces_libre: false, precisions: '', vigilance: '',
    meilleure_periode: '', derniere_verification: null, image: null, ...champs,
  };
}

describe('AdminLieuxComponent', () => {
  let fixture: ComponentFixture<AdminLieuxComponent>;
  let hote: HTMLElement;
  let service: { envoyerImageLieu: ReturnType<typeof vi.fn>; retirerImageLieu: ReturnType<typeof vi.fn> };
  let reponse: LieuDetente[];

  const noms = (): string[] => [...hote.querySelectorAll('.al__nom')].map((n) => n.textContent!.trim());
  const texte = (): string => hote.textContent!.replace(/\s+/g, ' ');
  const bouton = (libelle: string): HTMLButtonElement =>
    [...hote.querySelectorAll('button')].find((b) => b.textContent!.includes(libelle))!;

  function servir(): void {
    TestBed.inject(HttpTestingController).match(`${API_BASE_URL}/lieux`).forEach((r) => r.flush(reponse));
  }

  async function terminer(): Promise<void> {
    for (let i = 0; i < 5; i++) {
      await new Promise((r) => setTimeout(r));
      fixture.detectChanges();
      TestBed.tick();
      servir();
    }
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function choisir(fichier: File, indice = 0): Promise<void> {
    const champ = hote.querySelectorAll<HTMLInputElement>('input[type=file]')[indice];
    Object.defineProperty(champ, 'files', { value: [fichier], configurable: true });
    champ.dispatchEvent(new Event('change'));
    await terminer();
  }

  async function filtrer(valeur: string): Promise<void> {
    const champ = hote.querySelector<HTMLSelectElement>('#al-photo')!;
    champ.value = valeur;
    champ.dispatchEvent(new Event('change'));
    await terminer();
  }

  const jpeg = (taille = 10): File => new File([new Uint8Array(taille)], 'photo.jpg', { type: 'image/jpeg' });

  beforeEach(async () => {
    reponse = [
      lieu(1, 'Mont Assirik'),
      lieu(2, 'Cascade de Ségou', { region: 'Kédougou' }),
      lieu(3, 'Forêt de Sefa', { region: 'Sédhiou', ville: 'Sédhiou' }),
      lieu(4, 'Lac Rose (Lac Retba)', { region: 'Dakar' }), // photo livrée avec le site
      lieu(5, 'Grottes de Dandé', { image: 'http://api/media/lieux/dande.jpg' }), // photo envoyée
    ];
    service = {
      envoyerImageLieu: vi.fn().mockResolvedValue(undefined),
      retirerImageLieu: vi.fn().mockResolvedValue(undefined),
    };
    await TestBed.configureTestingModule({
      imports: [AdminLieuxComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AdministrationService, useValue: service },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(AdminLieuxComponent);
    hote = fixture.nativeElement;
    await terminer();
  });

  it('s’ouvre sur les lieux sans photo et dit combien il en reste', () => {
    expect(noms()).toEqual(['Mont Assirik', 'Cascade de Ségou', 'Forêt de Sefa']);
    expect(texte()).toContain('3 lieux sans photo sur 5');
    expect(hote.querySelector<HTMLSelectElement>('#al-photo')!.value).toBe('SANS');
  });

  it('rappelle quelle photo envoyer', () => {
    expect(texte()).toContain('Photo réelle du lieu, au Sénégal, dont vous avez les droits');
  });

  it('filtre par présence de photo', async () => {
    await filtrer('AVEC');
    expect(noms()).toEqual(['Lac Rose (Lac Retba)', 'Grottes de Dandé']);
    await filtrer('TOUTES');
    expect(noms()).toHaveLength(5);
  });

  it('filtre par région', async () => {
    const champ = hote.querySelector<HTMLSelectElement>('#al-region')!;
    champ.value = 'Sédhiou';
    champ.dispatchEvent(new Event('change'));
    await terminer();
    expect(noms()).toEqual(['Forêt de Sefa']);
  });

  it('cherche sans tenir compte des accents ni des majuscules', async () => {
    const champ = hote.querySelector<HTMLInputElement>('#al-recherche')!;
    champ.value = 'SEGOU';
    champ.dispatchEvent(new Event('input'));
    await terminer();
    expect(noms()).toEqual(['Cascade de Ségou']);
  });

  it('un lieu de l’adresse est retrouvé à l’ouverture', async () => {
    fixture.componentRef.setInput('q', 'Grottes de Dandé');
    fixture.componentRef.setInput('photo', 'TOUTES');
    await terminer();
    expect(noms()).toEqual(['Grottes de Dandé']);
  });

  it('envoie le fichier choisi et le lieu quitte la liste', async () => {
    reponse = reponse.map((l) => (l.id === 1 ? { ...l, image: 'http://api/media/lieux/a.jpg' } : l));
    const fichier = jpeg();
    await choisir(fichier);
    expect(service.envoyerImageLieu).toHaveBeenCalledWith(1, fichier);
    expect(noms()).toEqual(['Cascade de Ségou', 'Forêt de Sefa']);
    expect(texte()).toContain('2 lieux sans photo sur 5');
    expect(hote.querySelector('[role=status]')!.textContent).toContain('Photo enregistrée pour Mont Assirik');
  });

  it('vérifie le format avant l’envoi', async () => {
    await choisir(new File(['x'], 'photo.heic', { type: 'image/heic' }));
    expect(service.envoyerImageLieu).not.toHaveBeenCalled();
    expect(hote.querySelector('[role=alert]')!.textContent).toContain('JPEG, PNG ou WebP');
  });

  it('vérifie la taille avant l’envoi', async () => {
    await choisir(jpeg(5 * 1024 * 1024 + 1));
    expect(service.envoyerImageLieu).not.toHaveBeenCalled();
    expect(hote.querySelector('[role=alert]')!.textContent).toContain('5 Mo');
  });

  it('affiche l’erreur renvoyée par le serveur', async () => {
    service.envoyerImageLieu.mockRejectedValue(
      new HttpErrorResponse({ status: 400, error: { image: ["Ce fichier n'est pas une image lisible."] } }),
    );
    await choisir(jpeg());
    expect(hote.querySelector('[role=alert]')!.textContent).toContain("Ce fichier n'est pas une image lisible.");
    expect(noms()).toContain('Mont Assirik');
  });

  it('une panne réseau donne un message compréhensible', async () => {
    service.envoyerImageLieu.mockRejectedValue(new HttpErrorResponse({ status: 0 }));
    await choisir(jpeg());
    expect(hote.querySelector('[role=alert]')!.textContent).toContain('Envoi impossible');
  });

  it('une photo envoyée peut être remplacée ou retirée', async () => {
    await filtrer('AVEC');
    expect(bouton('Retirer')).toBeDefined();
    reponse = reponse.map((l) => (l.id === 5 ? { ...l, image: null } : l));
    bouton('Retirer').click();
    await terminer();
    expect(service.retirerImageLieu).toHaveBeenCalledWith(5);
    expect(noms()).toEqual(['Lac Rose (Lac Retba)']);
  });

  it('une photo livrée avec le site se remplace, mais ne se retire pas', async () => {
    const champ = hote.querySelector<HTMLInputElement>('#al-recherche')!;
    champ.value = 'lac rose';
    champ.dispatchEvent(new Event('input'));
    await filtrer('AVEC');
    expect(noms()).toEqual(['Lac Rose (Lac Retba)']);
    expect(bouton('Retirer')).toBeUndefined();
    expect(texte()).toContain('Remplacer');
    expect(hote.querySelector<HTMLImageElement>('.al__vignette img')!.alt).toContain('Lac Rose');
  });

  it('un lieu sans photo montre sa couverture', () => {
    expect(hote.querySelector('.al__vignette ss-couverture-lieu')).not.toBeNull();
    expect(hote.querySelector('.al__vignette img')).toBeNull();
    expect(texte()).toContain('Ajouter une photo');
  });

  it('les champs de fichier ont un libellé propre à chaque lieu', () => {
    const champ = hote.querySelector<HTMLInputElement>('input[type=file]')!;
    expect(champ.getAttribute('aria-label')).toBe('Ajouter une photo pour Mont Assirik');
    expect(champ.accept).toContain('.webp');
  });

  it('félicite quand tous les lieux ont leur photo', async () => {
    reponse = reponse.map((l) => ({ ...l, image: 'http://api/media/lieux/a.jpg' }));
    await choisir(jpeg());
    expect(noms()).toEqual([]);
    expect(texte()).toContain('Tous les lieux ont une photo');
  });
});
