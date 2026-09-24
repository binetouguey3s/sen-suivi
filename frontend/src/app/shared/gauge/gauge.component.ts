import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

const RAYON = 90;
const CIRCONFERENCE = 2 * Math.PI * RAYON;

// Jauge circulaire (ss-gauge). Jamais rouge, quel que soit le score.
@Component({
  selector: 'ss-gauge',
  standalone: true,
  template: `
    <div class="gauge">
      <svg viewBox="0 0 200 200" aria-hidden="true" focusable="false">
        <circle class="gauge__piste" cx="100" cy="100" [attr.r]="rayon" />
        <circle
          class="gauge__valeur"
          cx="100"
          cy="100"
          [attr.r]="rayon"
          [attr.stroke-dasharray]="circonference"
          [attr.stroke-dashoffset]="decalage()"
        />
      </svg>
      <div class="gauge__texte" role="img" [attr.aria-label]="'Score total : ' + valeur() + ' pour cent'">
        <span class="gauge__nombre">{{ valeur() }}%</span>
        <span class="gauge__legende">Score total</span>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: inline-block;
      }
      .gauge {
        position: relative;
        width: 200px;
        height: 200px;
      }
      svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }
      circle {
        fill: none;
        stroke-width: 12;
      }
      .gauge__piste {
        stroke: var(--ss-menthe-pale);
      }
      .gauge__valeur {
        stroke: var(--ss-bleu-sen-suivi);
        stroke-linecap: round;
      }
      .gauge__texte {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
      .gauge__nombre {
        font-family: var(--ss-police-titres);
        font-weight: var(--ss-poids-titre-fort);
        font-size: 44px;
        line-height: var(--ss-hauteur-ligne-titre);
        color: var(--ss-bleu-sen-suivi);
        font-variant-numeric: tabular-nums;
      }
      .gauge__legende {
        font-size: 14px;
        color: var(--ss-gris-ardoise);
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GaugeComponent {
  readonly valeur = input.required<number>();

  protected readonly rayon = RAYON;
  protected readonly circonference = CIRCONFERENCE;
  protected readonly decalage = computed(
    () => CIRCONFERENCE * (1 - Math.min(100, Math.max(0, this.valeur())) / 100),
  );
}
