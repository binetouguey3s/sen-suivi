import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Component, input, output } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LieuDetente } from '../../core/models/suivi';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { RepertoireComponent } from './repertoire.component';

// Le premier test paie le démarrage du routeur et des composants : 5 s ne suffisent pas sur une machine chargée
vi.setConfig({ testTimeout: 30000 });

@Component({ selector: 'ss-carte-lieux', standalone: true, template: '' })
class CarteLieuxFactice {
  readonly lieux = input.required<LieuDetente[]>();
  readonly selection = input<number | null>(null);
  readonly compact = input(false);
  readonly choisi = output<number>();
  readonly ouvrir = output<number>();
}

function lieu(id: number, nom: string, champs: Partial<LieuDetente> = {}): LieuDetente {
  return {
    id, nom, region: 'Dakar', ville: 'Dakar', type_lieu: 'Plage', description: '.', categorie: 'Plages & littoral',
    latitude: null, longitude: null, acces: 'LIBRE', acces_libre: true, precisions: '', vigilance: '',
    meilleure_periode: '', derniere_verification: null, image: null, ...champs,
  };
}

const LIEUX = [
  lieu(1, 'Lac Rose (Lac Retba)', { categorie: 'Lacs & lagunes', acces: 'MIXTE', latitude: 14.8, longitude: -17.2 }),
  lieu(2, 'Pointe des Almadies', { latitude: 14.7, longitude: -17.5 }),
  lieu(3, 'Accrobaobab', { region: 'Thiès', ville: 'Sindia', categorie: 'Parcs & jardins', acces: 'PAYANT' }),
  lieu(4, 'Réserve de Mbour', { region: 'Thiès', ville: 'Mbour', categorie: 'Parcs nationaux & réserves', acces: 'RESTREINT' }),
  lieu(5, 'Basse Casamance', { region: 'Ziguinchor', ville: 'Oussouye', categorie: 'Parcs nationaux & réserves', acces: 'RESTREINT' }),
];

describe('RepertoireComponent', () => {
  let http: HttpTestingController;
  let harnais: RouterTestingHarness;

  const hote = (): HTMLElement => harnais.routeNativeElement!;
  const texte = (): string => hote().textContent!.replace(/\s+/g, ' ');
  const cartes = (): string[] => [...hote().querySelectorAll('.carte-lieu__nom')].map((n) => n.textContent!.trim());
  const bouton = (libelle: string): HTMLButtonElement =>
    [...hote().querySelectorAll('button')].find((b) => b.textContent!.replace(/\s+/g, ' ').trim().startsWith(libelle))!;
  const url = (): string => decodeURIComponent(TestBed.inject(Router).url).replace(/\+/g, ' ');

  // Répond comme l'API : filtres region, categorie, acces et q
  function repondre(): void {
    for (const requete of http.match(() => true)) {
      const p = new URL(requete.request.urlWithParams, 'http://x').searchParams;
      const acces = p.getAll('acces');
      const q = (p.get('q') ?? '').toLowerCase();
      requete.flush(
        LIEUX.filter((l) => !p.get('region') || l.region === p.get('region'))
          .filter((l) => !p.get('categorie') || l.categorie === p.get('categorie'))
          .filter((l) => !acces.length || acces.includes(l.acces))
          .filter((l) => l.nom.toLowerCase().includes(q)),
      );
    }
  }

  // whenStable() attend la fin des requêtes : il faut d'abord y répondre.
  // Plusieurs tours, car naviguer relance les requêtes en plusieurs temps
  async function stabiliser(): Promise<void> {
    for (let tour = 0; tour < 4; tour++) {
      await new Promise((fin) => setTimeout(fin));
      harnais.detectChanges();
      TestBed.tick();
      repondre();
    }
    await harnais.fixture.whenStable();
    harnais.detectChanges();
  }

  async function ouvrir(adresse: string): Promise<void> {
    harnais = await RouterTestingHarness.create();
    void TestBed.inject(Router).navigateByUrl(adresse);
    await stabiliser();
  }

  async function cliquer(libelle: string): Promise<void> {
    bouton(libelle).click();
    await stabiliser();
  }

  beforeEach(async () => {
    TestBed.overrideComponent(RepertoireComponent, {
      remove: { imports: [CarteLieuxComponent] },
      add: { imports: [CarteLieuxFactice] },
    });
    await TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'lieux', component: RepertoireComponent }, { path: 'lieux/:id', children: [] }], withComponentInputBinding()),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  it('masque les lieux fermés par défaut et le dit', async () => {
    await ouvrir('/lieux');
    expect(cartes()).toEqual(['Lac Rose (Lac Retba)', 'Pointe des Almadies', 'Accrobaobab']);
    expect(hote().querySelector<HTMLInputElement>('#rep-masquer')!.checked).toBe(true);
    expect(texte()).toContain('2 lieux fermés masqués');
  });

  it('chercher un lieu fermé signale qu’il existe, et « Afficher » le révèle', async () => {
    await ouvrir('/lieux?q=basse');
    expect(cartes()).toEqual([]);
    expect(texte()).toContain('1 lieu fermé masqué');
    await cliquer('Afficher');
    expect(cartes()).toEqual(['Basse Casamance']);
    expect(url()).toContain('ouverts=0');
    expect(hote().querySelector('.pastille-acces--RESTREINT')!.textContent).toContain('Restreint');
  });

  it('lit les filtres depuis l’adresse', async () => {
    await ouvrir('/lieux?region=Thiès&categorie=Parcs %26 jardins');
    expect(cartes()).toEqual(['Accrobaobab']);
    expect(hote().querySelector<HTMLSelectElement>('#rep-region')!.value).toBe('Thiès');
    expect(texte()).toContain('1 lieu trouvé · Thiès · Parcs & jardins');
  });

  it('écrit les filtres dans l’adresse', async () => {
    await ouvrir('/lieux');
    const region = hote().querySelector<HTMLSelectElement>('#rep-region')!;
    region.value = 'Thiès';
    region.dispatchEvent(new Event('change'));
    await stabiliser();
    expect(url()).toContain('region=Thiès');
    await cliquer('Parcs & jardins');
    expect(url()).toContain('categorie=Parcs & jardins');
    await cliquer('Payant');
    expect(url()).toContain('acces=PAYANT');
    expect(cartes()).toEqual(['Accrobaobab']);
  });

  it('accepte plusieurs accès et une seconde pression retire le filtre', async () => {
    await ouvrir('/lieux');
    await cliquer('Payant');
    await cliquer('Mixte');
    expect(cartes()).toEqual(['Lac Rose (Lac Retba)', 'Accrobaobab']);
    await cliquer('Mixte');
    expect(cartes()).toEqual(['Accrobaobab']);
    expect(bouton('Payant').getAttribute('aria-pressed')).toBe('true');
    expect(bouton('Mixte').getAttribute('aria-pressed')).toBe('false');
  });

  it('la recherche passe dans l’adresse après la saisie', async () => {
    await ouvrir('/lieux');
    const champ = hote().querySelector<HTMLInputElement>('input[type=search]')!;
    expect(champ.placeholder).toBe('Rechercher un lieu, une ville, une région…');
    champ.value = 'lac';
    champ.dispatchEvent(new Event('input'));
    await new Promise((fin) => setTimeout(fin, 300));
    await stabiliser();
    expect(url()).toContain('q=lac');
    expect(cartes()).toEqual(['Lac Rose (Lac Retba)']);
  });

  it('la puce Restreint décoche « Masquer les lieux fermés »', async () => {
    await ouvrir('/lieux');
    await cliquer('Restreint');
    expect(hote().querySelector<HTMLInputElement>('#rep-masquer')!.checked).toBe(false);
    expect(cartes()).toEqual(['Réserve de Mbour', 'Basse Casamance']);
    await cliquer('Restreint');
    expect(hote().querySelector<HTMLInputElement>('#rep-masquer')!.checked).toBe(true);
  });

  it('recocher « Masquer » retire la puce Restreint', async () => {
    await ouvrir('/lieux?acces=RESTREINT');
    hote().querySelector<HTMLInputElement>('#rep-masquer')!.click();
    await stabiliser();
    expect(url()).not.toContain('RESTREINT');
    expect(hote().querySelector<HTMLInputElement>('#rep-masquer')!.checked).toBe(true);
  });

  it('les nombres par région suivent la case', async () => {
    await ouvrir('/lieux');
    const options = (): string[] =>
      [...hote().querySelectorAll('#rep-region option')].map((o) => o.textContent!.trim());
    expect(options()).toContain('Thiès (1)');
    expect(options()[0]).toBe('Tout le Sénégal (3)');
    expect(options()).toHaveLength(15);
    hote().querySelector<HTMLInputElement>('#rep-masquer')!.click();
    await stabiliser();
    expect(options()).toContain('Thiès (2)');
    expect(options()[0]).toBe('Tout le Sénégal (5)');
  });

  it('montre les filtres actifs, retirables un à un ou tous ensemble', async () => {
    await ouvrir('/lieux?region=Thiès&acces=PAYANT');
    expect(bouton('Filtres').textContent).toContain('Filtres (2)');
    hote().querySelector<HTMLButtonElement>('button[aria-label="Retirer le filtre Thiès"]')!.click();
    await stabiliser();
    expect(url()).not.toContain('region');
    expect(url()).toContain('acces=PAYANT');
    await cliquer('Tout effacer');
    expect(url()).toBe('/lieux');
    expect(hote().querySelector('button[aria-label^="Retirer le filtre"]')).toBeNull();
  });

  it('état vide : le bouton efface les filtres', async () => {
    await ouvrir('/lieux?q=introuvable');
    expect(texte()).toContain('Aucun lieu ne correspond');
    await cliquer('Effacer les filtres');
    expect(url()).toBe('/lieux');
    expect(cartes()).toHaveLength(3);
  });

  it('un lieu sans photo reçoit une couverture, jamais une fausse image', async () => {
    await ouvrir('/lieux?q=accrobaobab');
    expect(hote().querySelector('.carte-lieu img')).toBeNull();
    expect(hote().querySelector('ss-couverture-lieu')).not.toBeNull();
  });

  it('un lieu avec photo l’affiche avec un texte de remplacement', async () => {
    await ouvrir('/lieux?q=lac');
    const image = hote().querySelector<HTMLImageElement>('.carte-lieu img')!;
    expect(image.getAttribute('src')).toBe('/images/lieux/lieu-lac-rose.webp');
    expect(image.alt).toContain('Lac Rose');
  });

  it('dit combien de lieux figurent sur la carte', async () => {
    await ouvrir('/lieux');
    expect(texte()).toContain('2 lieux affichés sur la carte');
  });

  it('le panneau de filtres se referme depuis son bouton de résultats', async () => {
    await ouvrir('/lieux');
    await cliquer('Filtres');
    expect(bouton('Filtres').getAttribute('aria-expanded')).toBe('true');
    await cliquer('Voir les 3 lieux');
    expect(bouton('Filtres').getAttribute('aria-expanded')).toBe('false');
  });

  it('rappelle que les tarifs sont indicatifs', async () => {
    await ouvrir('/lieux');
    expect(texte()).toContain('Tarifs indicatifs, à confirmer auprès des gestionnaires');
  });

  it('les filtres sont de vrais champs avec un libellé', async () => {
    await ouvrir('/lieux');
    expect(hote().querySelector('label[for=rep-region]')!.textContent).toContain('Région');
    expect(hote().querySelector('label[for=rep-masquer]')!.textContent).toContain('Masquer les lieux fermés');
    expect(bouton('Plages & littoral').tagName).toBe('BUTTON');
  });
});
