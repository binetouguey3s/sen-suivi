import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Component, input } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LieuDetente } from '../../core/models/suivi';
import { AuthService } from '../../core/services/auth.service';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { LieuComponent } from './lieu.component';

// Le premier test paie le démarrage du routeur et des composants : 5 s ne suffisent pas sur une machine chargée
vi.setConfig({ testTimeout: 30000 });

@Component({ selector: 'ss-carte-lieux', standalone: true, template: '' })
class CarteLieuxFactice {
  readonly lieux = input.required<LieuDetente[]>();
  readonly selection = input<number | null>(null);
  readonly compact = input(false);
}

function lieu(id: number, nom: string, champs: Partial<LieuDetente> = {}): LieuDetente {
  return {
    id, nom, region: 'Kédougou', ville: 'Dindéfélo', type_lieu: 'Cascade, forêt', description: 'Une cascade.',
    categorie: 'Cascades & montagnes', latitude: null, longitude: null, acces: 'PAYANT', acces_libre: false,
    precisions: 'Contribution communautaire', vigilance: '', meilleure_periode: '',
    derniere_verification: '2026-11-01', image: null, ...champs,
  };
}

const LIEUX: LieuDetente[] = [
  lieu(1, 'Cascade et RNC de Dindéfélo', { vigilance: 'Feux de brousse signalés en mars 2026.', latitude: 12.36, longitude: -12.33 }),
  lieu(2, 'Mont Assirik', { precisions: 'Permis DPN', meilleure_periode: 'Saison sèche' }),
  lieu(3, 'Lac Rose (Lac Retba)', { region: 'Dakar', ville: 'Niaga', categorie: 'Lacs & lagunes', acces: 'MIXTE', latitude: 14.8, longitude: -17.2 }),
  lieu(4, 'Réserve écologique expérimentale de Mbour', { region: 'Thiès', ville: 'Mbour', acces: 'RESTREINT', precisions: 'Sur autorisation' }),
  lieu(5, 'Parc National de Basse Casamance', { region: 'Ziguinchor', ville: 'Oussouye', acces: 'RESTREINT', precisions: 'Actuellement non visitable', vigilance: 'Vérifiez auprès de la DPN.' }),
  lieu(6, 'Cascade de Ségou', { latitude: 12.4, longitude: -12.3 }),
  lieu(7, 'Grottes de Dandé', { latitude: 12.9, longitude: -12.4 }),
  lieu(8, 'Fleuve Gambie', { categorie: 'Fleuves & mangroves' }),
  lieu(9, 'Site fermé de la région', { acces: 'RESTREINT', latitude: 12.36, longitude: -12.34 }),
  lieu(10, 'Plages publiques', { region: 'Dakar', ville: 'Dakar', categorie: 'Plages & littoral', acces: 'GRATUIT', precisions: 'Gratuit (transats/clubs payants)' }),
  lieu(11, 'Lieu sans précisions', { acces: 'LIBRE', precisions: '' }),
];

describe('LieuComponent', () => {
  let http: HttpTestingController;
  let harnais: RouterTestingHarness;

  const hote = (): HTMLElement => harnais.routeNativeElement!;
  const texte = (): string => hote().textContent!.replace(/\s+/g, ' ');
  const lien = (libelle: string): HTMLAnchorElement =>
    [...hote().querySelectorAll('a')].find((a) => a.textContent!.includes(libelle))!;
  const bouton = (libelle: string): HTMLButtonElement =>
    [...hote().querySelectorAll('button')].find((b) => b.textContent!.includes(libelle))!;

  function repondre(): void {
    for (const requete of http.match(() => true)) {
      const adresse = new URL(requete.request.urlWithParams, 'http://x');
      const detail = adresse.pathname.match(/\/lieux\/(\d+)$/);
      if (detail) {
        const trouve = LIEUX.find((l) => l.id === Number(detail[1]));
        if (trouve) requete.flush(trouve);
        else requete.flush({}, { status: 404, statusText: 'Introuvable' });
      } else {
        const region = adresse.searchParams.get('region');
        requete.flush(LIEUX.filter((l) => !region || l.region === region));
      }
    }
  }

  async function stabiliser(): Promise<void> {
    for (let tour = 0; tour < 5; tour++) {
      await new Promise((fin) => setTimeout(fin));
      harnais.detectChanges();
      TestBed.tick();
      repondre();
    }
    await harnais.fixture.whenStable();
    harnais.detectChanges();
  }

  async function ouvrir(id: number): Promise<void> {
    harnais = await RouterTestingHarness.create();
    void TestBed.inject(Router).navigateByUrl(`/lieux/${id}`);
    await stabiliser();
  }

  beforeEach(async () => {
    TestBed.overrideComponent(LieuComponent, {
      remove: { imports: [CarteLieuxComponent] },
      add: { imports: [CarteLieuxFactice] },
    });
    await TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'lieux/:id', component: LieuComponent }, { path: 'lieux', children: [] }, { path: 'ressources', children: [] }, { path: 'admin/lieux', children: [] }], withComponentInputBinding()),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe('en-tête', () => {
    it('affiche le fil d’Ariane, le nom, la catégorie et l’accès', async () => {
      await ouvrir(1);
      const ariane = hote().querySelector('nav[aria-label="Fil d’Ariane"]')!;
      expect(ariane.textContent!.replace(/\s+/g, ' ')).toContain('Lieux');
      expect(ariane.textContent).toContain('Kédougou');
      expect(ariane.textContent).toContain('Dindéfélo');
      expect(lien('Kédougou').getAttribute('href')).toContain('/lieux?region=K');
      expect(hote().querySelector('h1')!.textContent).toContain('Cascade et RNC de Dindéfélo');
      expect(hote().querySelector('.lieu__hero .pastille-acces--PAYANT')).not.toBeNull();
      expect(hote().querySelector('.lieu__hero')!.textContent).toContain('Cascades & montagnes');
    });

    it('ne répète pas la localité quand elle est identique à la région', async () => {
      await ouvrir(10);
      const ariane = hote().querySelector('nav[aria-label="Fil d’Ariane"]')!;
      expect([...ariane.querySelectorAll('a, span')].map((e) => e.textContent!.trim())).toEqual(['Lieux', 'Dakar']);
    });

    it('le badge d’accès de l’en-tête est prévu pour un fond de photo', async () => {
      await ouvrir(10);
      expect(hote().querySelector('.lieu__hero .pastille-acces--sur-photo')!.textContent).toContain('Gratuit');
    });

    it('montre la photo avec un texte de remplacement', async () => {
      await ouvrir(3);
      const image = hote().querySelector<HTMLImageElement>('.lieu__hero img')!;
      expect(image.getAttribute('src')).toBe('/images/lieux/lieu-lac-rose.webp');
      expect(image.alt).toContain('Lac Rose');
    });

    it('sans photo, montre la couverture de la catégorie et aucune image', async () => {
      await ouvrir(1);
      expect(hote().querySelector('.lieu__hero img')).toBeNull();
      expect(hote().querySelector('.lieu__hero ss-couverture-lieu')).not.toBeNull();
    });
  });

  describe('itinéraire', () => {
    it('vise les coordonnées quand elles existent', async () => {
      await ouvrir(1);
      expect(lien('Itinéraire').href).toBe('https://www.google.com/maps/dir/?api=1&destination=12.36,-12.33');
    });

    it('cherche le nom et la localité sinon', async () => {
      await ouvrir(2);
      expect(lien('Itinéraire').href).toContain('google.com/maps/search/?api=1&query=Mont%20Assirik%20Dind');
    });
  });

  describe('partage', () => {
    it('utilise le partage natif quand il existe', async () => {
      const share = vi.fn().mockResolvedValue(undefined);
      vi.stubGlobal('navigator', { ...navigator, share });
      await ouvrir(1);
      bouton('Partager').click();
      await stabiliser();
      expect(share).toHaveBeenCalledOnce();
      expect(share.mock.calls[0][0].title).toBe('Cascade et RNC de Dindéfélo');
    });

    it('copie le lien sinon et le confirme', async () => {
      const writeText = vi.fn().mockResolvedValue(undefined);
      vi.stubGlobal('navigator', { clipboard: { writeText } });
      await ouvrir(1);
      bouton('Partager').click();
      await stabiliser();
      expect(writeText).toHaveBeenCalledOnce();
      expect(texte()).toContain('Lien copié');
    });

    it('annuler le partage natif n’affiche aucune erreur', async () => {
      const share = vi.fn().mockRejectedValue(new DOMException('annulé', 'AbortError'));
      vi.stubGlobal('navigator', { share });
      await ouvrir(1);
      bouton('Partager').click();
      await stabiliser();
      expect(texte()).not.toContain('Lien copié');
      expect(texte()).not.toContain('impossible');
    });
  });

  describe('bandeau de vigilance', () => {
    const bandeau = (): Element | null => hote().querySelector('.lieu__vigilance');

    it('reprend la vigilance du lieu', async () => {
      await ouvrir(1);
      expect(bandeau()!.textContent).toContain('Feux de brousse signalés en mars 2026.');
    });

    it('n’apparaît pas sans vigilance sur un lieu ouvert', async () => {
      await ouvrir(2);
      expect(bandeau()).toBeNull();
    });

    it('Réserve de Mbour : dit « sur autorisation », jamais « non visitable »', async () => {
      await ouvrir(4);
      expect(bandeau()!.textContent).toContain('Sur autorisation');
      expect(bandeau()!.textContent).toContain('Renseignez-vous avant de vous déplacer');
      expect(bandeau()!.textContent).not.toContain('non visitable');
    });

    it('Basse Casamance : donne la situation du PDF et sa vigilance', async () => {
      await ouvrir(5);
      expect(bandeau()!.textContent).toContain('Actuellement non visitable');
      expect(bandeau()!.textContent).toContain('Vérifiez auprès de la DPN.');
    });
  });

  describe('l’essentiel', () => {
    const essentiel = (): string => hote().querySelector('.lieu__essentiel')!.textContent!.replace(/\s+/g, ' ');

    it('donne la région, la localité, le type et l’accès avec ses précisions', async () => {
      await ouvrir(1);
      for (const attendu of ['Kédougou', 'Dindéfélo', 'Cascade, forêt', 'Contribution communautaire']) {
        expect(essentiel()).toContain(attendu);
      }
    });

    it('suit l’ordre Région, Localité, Accès, Type, Meilleure période', async () => {
      await ouvrir(2);
      const libelles = [...hote().querySelectorAll('.lieu__essentiel li > div > span')].map((e) => e.textContent!.trim());
      expect(libelles).toEqual(['Région', 'Localité', 'Accès', 'Type de lieu', 'Meilleure période']);
    });

    it('ne répète pas le badge d’accès, seulement le texte des précisions', async () => {
      await ouvrir(10);
      expect(hote().querySelector('.lieu__essentiel .pastille-acces')).toBeNull();
      expect(essentiel()).toContain('Gratuit (transats/clubs payants)');
    });

    it('sans précisions, la ligne Accès donne le type d’accès plutôt que de rester vide', async () => {
      await ouvrir(11);
      expect(essentiel()).toContain('Accès libre');
    });

    it('porte les boutons Itinéraire et Partager', async () => {
      await ouvrir(1);
      const bloc = hote().querySelector('.lieu__essentiel')!;
      expect(bloc.querySelector('a[target=_blank]')!.textContent).toContain('Itinéraire');
      expect([...bloc.querySelectorAll('button')].map((b) => b.textContent!.trim())).toEqual(['Partager']);
    });

    it('ajoute la note DPN seulement si les précisions citent le permis', async () => {
      await ouvrir(2);
      expect(essentiel()).toContain('3 000 FCFA');
      expect(essentiel()).toContain('décret 2015-1194');
    });

    it('n’ajoute pas la note DPN aux autres lieux', async () => {
      await ouvrir(1);
      expect(essentiel()).not.toContain('FCFA');
    });

    it('n’affiche la meilleure période que si elle est renseignée', async () => {
      await ouvrir(2);
      expect(essentiel()).toContain('Saison sèche');
    });

    it('n’a pas de ligne de période sans valeur', async () => {
      await ouvrir(1);
      expect(essentiel()).not.toContain('Meilleure période');
    });

    it('ne mentionne jamais une vérification sur la page publique', async () => {
      await ouvrir(1);
      expect(texte()).not.toMatch(/vérifiées|répertoire de novembre|novembre 2026/i);
    });
  });

  describe('organisation de la page', () => {
    const avant = (a: string, b: string): boolean =>
      !!(hote().querySelector(a)!.compareDocumentPosition(hote().querySelector(b)!) & Node.DOCUMENT_POSITION_FOLLOWING);

    it('la colonne principale commence par le bandeau, puis la description et le bien-être', async () => {
      await ouvrir(1);
      const principale = hote().querySelector('.lieu__principale')!;
      expect(principale.querySelector('.lieu__vigilance')).not.toBeNull();
      expect(avant('.lieu__vigilance', '.lieu__description')).toBe(true);
      expect(avant('.lieu__description', '.lieu__bien-etre')).toBe(true);
    });

    it('la colonne latérale porte l’essentiel puis la mini-carte, la principale aucune carte', async () => {
      await ouvrir(1);
      expect(hote().querySelector('aside.lieu__laterale .lieu__essentiel')).not.toBeNull();
      expect(hote().querySelector('aside.lieu__laterale .lieu__mini-carte ss-carte-lieux')).not.toBeNull();
      expect(hote().querySelector('.lieu__principale ss-carte-lieux')).toBeNull();
      expect(avant('.lieu__essentiel', '.lieu__mini-carte')).toBe(true);
    });

    it('sous la carte, un lien ouvre le lieu dans Google Maps', async () => {
      await ouvrir(1);
      const ouvrirCarte = lien('Ouvrir dans Google Maps');
      expect(ouvrirCarte.href).toBe('https://www.google.com/maps/search/?api=1&query=12.36,-12.33');
      expect(ouvrirCarte.target).toBe('_blank');
      expect(avant('.lieu__mini-carte', '.lieu__lien-carte')).toBe(true);
    });

    it('sans coordonnées, ni carte ni lien vers Google Maps', async () => {
      await ouvrir(2);
      expect(lien('Ouvrir dans Google Maps')).toBeUndefined();
    });

    it('chaque carte de contenu a le même en-tête : une icône et son titre', async () => {
      await ouvrir(1);
      for (const bloc of ['.lieu__description', '.lieu__bien-etre', '.lieu__essentiel']) {
        const entete = hote().querySelector(`${bloc} .lieu__bloc-entete`)!;
        expect(entete.querySelector('.lieu__icone')).not.toBeNull();
        expect(entete.querySelector('h2')).not.toBeNull();
      }
    });

    it('le lien vers Google Maps fait partie de la carte', async () => {
      await ouvrir(1);
      expect(hote().querySelector('.lieu__carte-bloc.lieu__bloc .lieu__lien-carte')).not.toBeNull();
    });

    it('les suggestions prennent toute la largeur quand il n’y a pas de carte', async () => {
      await ouvrir(2);
      expect(hote().querySelector('.lieu__grille--sans-carte')).not.toBeNull();
    });

    it('avec une carte, les suggestions partagent la rangée', async () => {
      await ouvrir(1);
      expect(hote().querySelector('.lieu__grille--sans-carte')).toBeNull();
    });

    it('« À découvrir aussi » suit le bien-être dans la colonne principale, pour équilibrer la page', async () => {
      await ouvrir(1);
      expect(hote().querySelector('.lieu__principale .lieu__suggestions')).not.toBeNull();
      expect(avant('.lieu__bien-etre', '.lieu__suggestions')).toBe(true);
    });

    it('les tarifs restent sous les deux colonnes', async () => {
      await ouvrir(1);
      expect(hote().querySelector('.lieu__grille .lieu__mention')).toBeNull();
      expect(avant('.lieu__grille', '.lieu__mention')).toBe(true);
    });
  });

  it('affiche la description', async () => {
    await ouvrir(1);
    expect(texte()).toContain('Une cascade.');
  });

  it('propose un conseil de bien-être et une thématique existante', async () => {
    await ouvrir(3);
    const bloc = hote().querySelector('.lieu__bien-etre')!;
    expect(bloc.textContent).toContain('Pour votre bien-être sur place');
    expect(lien('Explorer').getAttribute('href')).toBe('/ressources?thematique=Respiration');
  });

  it('n’affiche la mini-carte qu’avec des coordonnées', async () => {
    await ouvrir(1);
    expect(hote().querySelector('ss-carte-lieux')).not.toBeNull();
  });

  it('n’a pas de mini-carte sans coordonnées', async () => {
    await ouvrir(2);
    expect(hote().querySelector('ss-carte-lieux')).toBeNull();
  });

  it('« À découvrir aussi » : 3 lieux de la région, ni le lieu courant ni un lieu restreint', async () => {
    await ouvrir(1);
    const section = hote().querySelector('.lieu__suggestions')!;
    expect(section.querySelector('h2')!.textContent).toContain('À découvrir aussi en région Kédougou');
    const noms = [...section.querySelectorAll('.carte-lieu__nom')].map((n) => n.textContent!.trim());
    expect(noms).toEqual(['Cascade de Ségou', 'Grottes de Dandé', 'Mont Assirik']);
  });

  describe('lien vers les photos', () => {
    const comme = (type: string | null): void => {
      vi.spyOn(TestBed.inject(AuthService), 'typeCompte').mockReturnValue(type as never);
    };

    it('reste invisible du public et des utilisateurs', async () => {
      comme('utilisateur');
      await ouvrir(1);
      expect(lien('photo')).toBeUndefined();
    });

    it('propose à l’administration d’ajouter la photo d’un lieu qui n’en a pas', async () => {
      comme('administrateur');
      await ouvrir(1);
      const adresse = decodeURIComponent(lien('Ajouter une photo').getAttribute('href')!).replace(/\+/g, ' ');
      expect(adresse).toContain('/admin/lieux');
      expect(adresse).toContain('q=Cascade et RNC de Dindéfélo');
    });

    it('propose de changer la photo d’un lieu qui en a une', async () => {
      comme('administrateur');
      await ouvrir(3);
      expect(lien('Changer la photo').getAttribute('href')).toContain('photo=TOUTES');
    });
  });

  it('rappelle que les tarifs sont indicatifs', async () => {
    await ouvrir(1);
    expect(texte()).toContain('Tarifs indicatifs, à confirmer auprès des gestionnaires.');
  });

  it('garde l’accès à l’aide immédiate', async () => {
    await ouvrir(1);
    expect(bouton('Besoin d\'aide tout de suite')).toBeDefined();
  });

  it('affiche un squelette pendant le chargement, pas un simple texte', async () => {
    harnais = await RouterTestingHarness.create();
    void TestBed.inject(Router).navigateByUrl('/lieux/1');
    await new Promise((fin) => setTimeout(fin));
    harnais.detectChanges();
    expect(hote().querySelector('.lieu__squelette')).not.toBeNull();
    expect(hote().querySelector('.lieu__etat')).toBeNull();
    await stabiliser();
  });

  it('revient en haut de page en passant à un autre lieu', async () => {
    const defiler = vi.fn();
    vi.stubGlobal('scrollTo', defiler);
    await ouvrir(1);
    defiler.mockClear();
    void TestBed.inject(Router).navigateByUrl('/lieux/2');
    await stabiliser();
    expect(defiler).toHaveBeenCalledWith(0, 0);
    expect(hote().querySelector('h1')!.textContent).toContain('Mont Assirik');
  });

  it('dit quand le lieu est introuvable', async () => {
    await ouvrir(999);
    expect(texte()).toContain('Ce lieu est introuvable');
    expect(lien('Retour au répertoire').getAttribute('href')).toBe('/lieux');
  });
});
