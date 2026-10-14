import { describe, expect, it } from 'vitest';

import { ProfilOnboarding } from '../../core/models/onboarding';
import { jourDeLAnnee } from '../../core/utils/jour';
import { CONSEILS, conseilDuJour } from './conseils';

function profil(preoccupations: string[]): ProfilOnboarding {
  return {
    version: 1, statut: 'termine', date: '2026-10-01', preoccupations, rien_de_particulier: false,
    bien_etre: [], spiritualite: [], moments: [], formats: [], rappels: true, metiers: [],
  };
}

describe('Conseil du jour', () => {
  it('compte 30 conseils, courts et au vouvoiement', () => {
    expect(CONSEILS).toHaveLength(30);
    for (const c of CONSEILS) {
      expect(c.texte.length).toBeLessThanOrEqual(220);
      expect(c.texte).not.toMatch(/\b(tu|ton|ta|tes|toi)\b/i);
      expect(c.texte).not.toMatch(/guéri|traitement|médicament/i);
    }
  });

  it('reste le même toute la journée et change le lendemain', () => {
    const matin = new Date(2026, 9, 14, 7, 0);
    const soir = new Date(2026, 9, 14, 23, 30);
    expect(conseilDuJour(matin, undefined, false)).toBe(conseilDuJour(soir, undefined, false));
    expect(conseilDuJour(new Date(2026, 9, 15, 9), undefined, false)).not.toBe(conseilDuJour(matin, undefined, false));
  });

  it('sans consentement : jour de l’année modulo 30', () => {
    const date = new Date(2026, 9, 14, 12);
    expect(conseilDuJour(date, profil(['sommeil']), false)).toBe(CONSEILS[jourDeLAnnee(date) % 30]);
  });

  it('avec consentement : un conseil qui répond à une préoccupation, chaque jour', () => {
    for (let jour = 1; jour <= 10; jour++) {
      const conseil = conseilDuJour(new Date(2026, 0, jour, 12), profil(['sommeil']), true);
      expect(conseil.thematique).toBe('Sommeil');
    }
  });

  it('« Un autre conseil » passe au suivant, et fait le tour de tous', () => {
    const date = new Date(2026, 9, 14, 12);
    const vus = new Set(Array.from({ length: 30 }, (_, n) => conseilDuJour(date, profil(['stress']), true, n)));
    expect(vus.size).toBe(30);
    expect(conseilDuJour(date, undefined, false, 1)).toBe(CONSEILS[(jourDeLAnnee(date) + 1) % 30]);
  });
});
