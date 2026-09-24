import { ChangeDetectionStrategy, Component } from '@angular/core';

// Signature de marque : courbe d'humeur menthe, trait
// plein de 3px aux extrémités arrondies. Décorative, absente des écrans de données.
@Component({
  selector: 'ss-courbe-marque',
  standalone: true,
  template: `
    <svg viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <path d="M0 70 C 180 20, 300 110, 520 70 S 900 20, 1120 65 S 1340 100, 1440 60" />
    </svg>
  `,
  styles: [
    `
      :host {
        display: block;
        pointer-events: none;
        line-height: 0;
      }
      svg {
        width: 100%;
        height: 100%;
      }
      path {
        fill: none;
        stroke: var(--ss-menthe);
        stroke-width: 3;
        stroke-linecap: round;
        opacity: 0.6;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CourbeMarqueComponent {}
