import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { AreaChartModule, Color, LineChartModule, ScaleType } from '@swimlane/ngx-charts';
import { curveBasis } from 'd3-shape';

// Mini-courbe décorative des cartes de statistiques (ss-sparkline), sans axe
// ni info-bulle. ngx-charts dessine la surface et le trait dans deux graphiques
// superposés, sur la même échelle : le graphique en aire ne trace pas de trait.
@Component({
  selector: 'ss-sparkline',
  standalone: true,
  imports: [AreaChartModule, LineChartModule],
  templateUrl: './sparkline.component.html',
  styleUrl: './sparkline.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SparklineComponent {
  private readonly document = inject(DOCUMENT);

  readonly valeurs = input.required<number[]>();

  protected readonly courbe = curveBasis;

  // ngx-charts attend une couleur réelle : on la lit dans les tokens plutôt
  // que de l'écrire en dur.
  protected readonly palette: Color = {
    name: 'sen-suivi',
    selectable: false,
    group: ScaleType.Ordinal,
    domain: [getComputedStyle(this.document.documentElement).getPropertyValue('--ss-menthe').trim()],
  };

  protected readonly series = computed(() => [
    { name: 'serie', series: this.valeurs().map((value, i) => ({ name: String(i), value })) },
  ]);

  // Marge au-dessus du point le plus haut, et une échelle non nulle quand
  // toutes les valeurs valent zéro.
  protected readonly maximum = computed(() => Math.max(1, ...this.valeurs()) * 1.25);
}
