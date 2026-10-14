import { describe, expect, it } from 'vitest';

import { ProfilOnboarding } from '../models/onboarding';
import { Ressource } from '../models/suivi';
import { RAISON_NOUVEAUTE, suggererRessources } from './suggestions';

function ressource(id: number, thematique: string, type: Ressource['type_ressource'], duree: number, date: string): Ressource {
  return {
    id,
    titre: `Ressource ${id}`,
    type_ressource: type,
    thematique,
    contenu: '…',
    duree_lecture: duree,
    date_publication: date,
  } as Ressource;
}

const RESSOURCES = [
  ressource(1, 'Stress', 'ARTICLE', 6, '2026-09-01'),
  ressource(2, 'Respiration', 'EXERCICE', 3, '2026-09-02'),
  ressource(3, 'Sommeil', 'PODCAST', 12, '2026-09-03'),
  ressource(4, 'Famille', 'ARTICLE', 7, '2026-10-10'),
  ressource(5, 'Travail', 'ARTICLE', 5, '2026-10-12'),
  ressource(6, 'Bien-être', 'PODCAST', 8, '2026-10-11'),
];

function profil(reponses: Partial<ProfilOnboarding>): ProfilOnboarding {
  return {
    version: 1, statut: 'termine', date: '2026-10-01', preoccupations: [], rien_de_particulier: false,
    bien_etre: [], spiritualite: [], moments: [], formats: [], rappels: true, metiers: [], ...reponses,
  };
}

const ids = (s: { ressource: Ressource }[]) => s.map((x) => x.ressource.id);

describe('suggererRessources', () => {
  it('sans consentement : les 3 plus récentes, « Nouveauté »', () => {
    const resultat = suggererRessources(RESSOURCES, profil({ preoccupations: ['sommeil'] }), 'MAL', false);
    expect(ids(resultat)).toEqual([5, 6, 4]);
    expect(resultat.every((s) => s.raison === RAISON_NOUVEAUTE)).toBe(true);
  });

  it('sans onboarding : les 3 plus récentes', () => {
    expect(ids(suggererRessources(RESSOURCES, undefined, null, true))).toEqual([5, 6, 4]);
  });

  it('une préoccupation fait remonter ses thématiques, avec la raison', () => {
    const resultat = suggererRessources(RESSOURCES, profil({ preoccupations: ['stress', 'sommeil'] }), null, true);
    expect(ids(resultat)).toEqual([3, 2, 1]);
    expect(resultat[0].raison).toBe('Parce que vous avez choisi : Sommeil');
    expect(resultat[2].raison).toBe('Parce que vous avez choisi : Stress');
  });

  it('une humeur basse fait remonter un exercice qui apaise', () => {
    const resultat = suggererRessources(RESSOURCES, profil({}), 'TRES_MAL', true);
    expect(resultat[0].ressource.id).toBe(2);
    expect(resultat[0].raison).toBe('Pour vous apaiser aujourd’hui');
    // Un podcast « Bien-être » n'est pas un exercice : pas de bonus
    expect(suggererRessources(RESSOURCES, profil({}), 'BIEN', true)[0].raison).toBe(RAISON_NOUVEAUTE);
  });

  it('le format et la durée préférés comptent un point chacun', () => {
    const resultat = suggererRessources(RESSOURCES, profil({ formats: ['audio'], duree: '15+' }), null, true);
    expect(resultat[0].ressource.id).toBe(3);
    expect(resultat[0].points).toBe(2);
    expect(resultat[1]).toMatchObject({ points: 1, raison: 'Au format audio, comme vous aimez' });
    expect(resultat[1].ressource.id).toBe(6);
  });

  it('à points égaux, la plus récente passe devant', () => {
    const resultat = suggererRessources(RESSOURCES, profil({ preoccupations: ['travail', 'famille'] }), null, true);
    expect(ids(resultat).slice(0, 2)).toEqual([5, 4]);
  });

  it('une préoccupation compte plus que le format', () => {
    const resultat = suggererRessources(RESSOURCES, profil({ preoccupations: ['famille'], formats: ['audio'] }), null, true);
    expect(resultat[0].ressource.id).toBe(4);
  });
});
