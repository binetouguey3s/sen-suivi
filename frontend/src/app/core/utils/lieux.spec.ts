import { describe, expect, it } from 'vitest';

import { imageDuLieu } from '../config/images-lieux';
import { LieuDetente } from '../models/suivi';
import { avecPhotoDabord, lienCarte, lienItineraire, lieuxOuverts, suggestionsPour } from './lieux';

const base = { nom: 'Mont Assirik', ville: 'Niokolo-Koba', latitude: null, longitude: null, image: null } as LieuDetente;

describe('lienItineraire', () => {
  it('vise les coordonnées quand elles existent', () => {
    expect(lienItineraire({ ...base, latitude: 12.8, longitude: -12.7 })).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=12.8,-12.7',
    );
  });

  it('cherche le nom et la localité sinon, avec un encodage sûr', () => {
    expect(lienItineraire({ ...base, nom: 'Plages & co', ville: "Patte d'Oie" })).toBe(
      "https://www.google.com/maps/search/?api=1&query=Plages%20%26%20co%20Patte%20d'Oie%20S%C3%A9n%C3%A9gal",
    );
  });
});

describe('lienCarte', () => {
  it('montre le lieu dans Google Maps, sans calculer de trajet', () => {
    expect(lienCarte({ ...base, latitude: 12.8, longitude: -12.7 })).toBe(
      'https://www.google.com/maps/search/?api=1&query=12.8,-12.7',
    );
  });
});

describe('imageDuLieu', () => {
  it('préfère la photo envoyée par l’administration', () => {
    expect(imageDuLieu({ nom: 'Lac Rose (Lac Retba)', image: 'http://api/media/lieux/a.jpg' })).toBe('http://api/media/lieux/a.jpg');
  });

  it('retrouve la photo livrée sous le nouveau nom du lieu', () => {
    expect(imageDuLieu({ nom: 'lac rose (lac retba)', image: null })).toBe('/images/lieux/lieu-lac-rose.webp');
    expect(imageDuLieu({ nom: 'Réserve Naturelle de Popenguine', image: null })).toBe('/images/lieux/lieu-popenguine.webp');
  });

  it('ne renvoie rien pour un lieu sans photo', () => {
    expect(imageDuLieu({ nom: 'Mont Assirik', image: null })).toBeNull();
  });
});

describe('lieuxOuverts', () => {
  it('écarte les lieux restreints, même avec une photo, et garde les autres', () => {
    const acces = ['GRATUIT', 'LIBRE', 'PAYANT', 'MIXTE', 'RESTREINT'] as const;
    const lieux = acces.map((a) => ({ ...base, acces: a, image: 'http://api/media/a.jpg' }));
    expect(lieuxOuverts(lieux).map((l) => l.acces)).toEqual(['GRATUIT', 'LIBRE', 'PAYANT', 'MIXTE']);
  });
});

describe('avecPhotoDabord', () => {
  it('place les lieux avec photo en tête, sans changer l’ordre du reste', () => {
    const lieux = [
      { ...base, nom: 'Mont Assirik' },
      { ...base, nom: 'Lac Rose (Lac Retba)' },
      { ...base, nom: 'Forêt de Sefa' },
      { ...base, nom: 'Grottes de Dandé', image: 'http://api/media/a.jpg' },
    ];
    expect(avecPhotoDabord(lieux).map((l) => l.nom)).toEqual([
      'Lac Rose (Lac Retba)', 'Grottes de Dandé', 'Mont Assirik', 'Forêt de Sefa',
    ]);
  });
});

describe('suggestionsPour', () => {
  const lieu = (id: number, champs: Partial<LieuDetente> = {}): LieuDetente =>
    ({ ...base, id, acces: 'LIBRE', region: 'Dakar', categorie: 'Îles', ...champs });
  const ids = (l: LieuDetente[]): number[] => l.map((x) => x.id);

  it('trie par distance quand les coordonnées existent', () => {
    const courant = lieu(1, { latitude: 14, longitude: -17 });
    const liste = [courant, lieu(2, { latitude: 16, longitude: -15 }), lieu(3, { latitude: 14.1, longitude: -17 })];
    expect(ids(suggestionsPour(courant, liste))).toEqual([3, 2]);
  });

  it('sans coordonnées, préfère la même catégorie, sans fausser le tri', () => {
    const courant = lieu(1);
    const liste = [lieu(2, { categorie: 'Forêts' }), lieu(3), lieu(4, { categorie: 'Forêts' }), lieu(5)];
    expect(ids(suggestionsPour(courant, liste))).toEqual([3, 5, 2]);
  });

  it('place les lieux avec coordonnées avant les autres', () => {
    const courant = lieu(1, { latitude: 14, longitude: -17 });
    const liste = [lieu(2), lieu(3, { latitude: 16, longitude: -15, categorie: 'Forêts' })];
    expect(ids(suggestionsPour(courant, liste))).toEqual([3, 2]);
  });

  it('écarte le lieu courant, les lieux restreints et les autres régions, et se limite à 3', () => {
    const courant = lieu(1);
    const liste = [courant, lieu(2, { acces: 'RESTREINT' }), lieu(3, { region: 'Thiès' }), lieu(4), lieu(5), lieu(6), lieu(7)];
    expect(ids(suggestionsPour(courant, liste))).toEqual([4, 5, 6]);
  });
});
