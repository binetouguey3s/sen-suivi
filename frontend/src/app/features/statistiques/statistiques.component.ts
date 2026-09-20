import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { LIBELLE_TYPE_EVALUATION, TypeEvaluation } from '../../core/models/evaluation';
import { NIVEAUX_HUMEUR, NiveauHumeur, SuiviHumeur } from '../../core/models/suivi';
import { IconComponent } from '../../shared/icon/icon.component';
import { MoodChartComponent, PointHumeur } from '../../shared/mood-chart/mood-chart.component';
import { valeurs } from '../../core/utils/ressource';

interface AutoEvaluationListe {
  id: number;
  date: string;
  type_evaluation: TypeEvaluation;
  score_de_tendance: number;
}

const PERIODES = [
  { jours: 7, libelle: '7 jours' },
  { jours: 30, libelle: '30 jours' },
  { jours: 90, libelle: '3 mois' },
] as const;

const JOURS = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
const TYPES: TypeEvaluation[] = ['STRESS', 'ANXIETE', 'FATIGUE'];

function iso(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function scoreDe(niveau: NiveauHumeur): number {
  return NIVEAUX_HUMEUR.find((n) => n.valeur === niveau)!.score;
}

@Component({
  selector: 'ss-statistiques',
  standalone: true,
  imports: [RouterLink, IconComponent, MoodChartComponent],
  templateUrl: './statistiques.component.html',
  styleUrl: './statistiques.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatistiquesComponent {
  protected readonly periodes = PERIODES;
  protected readonly periode = signal<number>(30);
  protected readonly moisAffiche = signal(new Date(new Date().getFullYear(), new Date().getMonth(), 1));

  // Historique de 4 mois : sert au graphique, au calendrier et aux observations
  protected readonly suivi = httpResource<SuiviHumeur[]>(() => `${API_BASE_URL}/suivi-humeur?periode=130j`, {
    defaultValue: [],
  });
  private readonly evaluations = httpResource<AutoEvaluationListe[]>(() => `${API_BASE_URL}/auto-evaluations`, {
    defaultValue: [],
  });

  private readonly parDate = computed(() => new Map(valeurs(this.suivi).map((e) => [e.date, scoreDe(e.score_humeur)])));

  protected readonly points = computed<PointHumeur[]>(() => {
    const n = this.periode();
    const pts: PointHumeur[] = [];
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      pts.push({
        libelle: n <= 7 ? JOURS[d.getDay()].slice(0, 3) : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
        score: this.parDate().get(iso(d)) ?? null,
      });
    }
    return pts;
  });
  protected readonly pasEtiquettes = computed(() => (this.periode() <= 7 ? 1 : this.periode() <= 30 ? 5 : 15));

  protected readonly moyenne = computed(() => {
    const s = this.points().map((p) => p.score).filter((x): x is number => x !== null);
    return s.length ? s.reduce((a, b) => a + b, 0) / s.length : null;
  });

  // Dernier score de chaque type d'auto-évaluation
  protected readonly repartition = computed(() =>
    TYPES.map((type) => {
      const dernier = this.evaluations
        .value()
        .filter((e) => e.type_evaluation === type)
        .sort((a, b) => (a.date < b.date ? 1 : -1))[0];
      return { type, libelle: LIBELLE_TYPE_EVALUATION[type].replace(/^d(e |')/, ''), score: dernier ? Math.round(dernier.score_de_tendance) : null };
    }),
  );

  // Observations calculées sur les données de la personne uniquement
  protected readonly observations = computed<string[]>(() => {
    const entrees = [...valeurs(this.suivi)].sort((a, b) => (a.date < b.date ? -1 : 1));
    const resultats: string[] = [];

    const scores = entrees.map((e) => ({ date: e.date, score: scoreDe(e.score_humeur) }));
    let serie = 0;
    for (let i = scores.length - 1; i > 0 && scores[i].score >= scores[i - 1].score; i--) serie++;
    if (serie >= 2 && scores[scores.length - 1].score > scores[scores.length - 1 - serie].score) {
      resultats.push(`Votre humeur s'améliore depuis ${serie} jours.`);
    }

    const parJour: Record<number, number[]> = {};
    for (const e of scores) (parJour[new Date(`${e.date}T00:00:00`).getDay()] ??= []).push(e.score);
    const moyennes = Object.entries(parJour)
      .filter(([, v]) => v.length >= 2)
      .map(([j, v]) => ({ jour: Number(j), moy: v.reduce((a, b) => a + b, 0) / v.length }))
      .sort((a, b) => a.moy - b.moy);
    if (moyennes.length >= 2 && moyennes[0].moy < moyennes[moyennes.length - 1].moy) {
      resultats.push(`Votre humeur est plus basse le ${JOURS[moyennes[0].jour]}.`);
    }

    if (!resultats.length) resultats.push('Continuez à noter votre humeur : des tendances apparaîtront avec le temps.');
    return resultats;
  });

  protected readonly titreMois = computed(() =>
    this.moisAffiche().toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' }),
  );

  // Calendrier du mois : semaines commençant le lundi, jours hors mois en grisé
  protected readonly jours = computed(() => {
    const debut = this.moisAffiche();
    const decalage = (debut.getDay() + 6) % 7;
    const cases: { numero: number; hors: boolean; score: number | null; iso: string }[] = [];
    for (let i = 0; i < 42; i++) {
      const d = new Date(debut.getFullYear(), debut.getMonth(), 1 - decalage + i);
      if (i >= 35 && d.getMonth() !== debut.getMonth()) break;
      cases.push({ numero: d.getDate(), hors: d.getMonth() !== debut.getMonth(), score: this.parDate().get(iso(d)) ?? null, iso: iso(d) });
    }
    return cases;
  });

  protected changerMois(delta: number): void {
    const m = this.moisAffiche();
    this.moisAffiche.set(new Date(m.getFullYear(), m.getMonth() + delta, 1));
  }
}
