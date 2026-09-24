import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface PointHumeur {
  libelle: string;
  score: number | null; // 1 à 5, null = jour sans saisie (un trou, jamais un zéro)
}

const LARGEUR = 700;
const HAUTEUR = 200;
const MARGE = 16;

@Component({
  selector: 'ss-mood-chart',
  standalone: true,
  templateUrl: './mood-chart.component.html',
  styleUrl: './mood-chart.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MoodChartComponent {
  readonly points = input.required<PointHumeur[]>();
  readonly moyenne = input<number | null>(null);
  // Une étiquette sur `pas` (utile pour 30 ou 90 jours)
  readonly pas = input(1);

  protected readonly viewBox = `0 0 ${LARGEUR} ${HAUTEUR}`;

  private readonly coordonnees = computed(() => {
    const pts = this.points();
    const pas = pts.length > 1 ? (LARGEUR - 2 * MARGE) / (pts.length - 1) : 0;
    return pts.map((p, i) => ({
      x: MARGE + i * pas,
      y: p.score === null ? null : HAUTEUR - MARGE - ((p.score - 1) / 4) * (HAUTEUR - 2 * MARGE),
      libelle: p.libelle,
      score: p.score,
    }));
  });

  protected readonly segments = computed(() => {
    const coords = this.coordonnees();
    const chemins: string[] = [];
    let courant = '';
    for (const point of coords) {
      if (point.y === null) {
        if (courant) chemins.push(courant);
        courant = '';
        continue;
      }
      courant += courant ? ` L ${point.x} ${point.y}` : `M ${point.x} ${point.y}`;
    }
    if (courant) chemins.push(courant);
    return chemins;
  });

  protected readonly pointsVisibles = computed(() =>
    this.coordonnees().filter((p) => p.y !== null),
  );

  protected readonly etiquettes = computed(() =>
    this.coordonnees().map((p, i) => ({ ...p, libelle: i % this.pas() === 0 ? p.libelle : '' })),
  );

  protected readonly yMoyenne = computed(() => {
    const m = this.moyenne();
    if (m === null) return null;
    return HAUTEUR - MARGE - ((m - 1) / 4) * (HAUTEUR - 2 * MARGE);
  });
}
