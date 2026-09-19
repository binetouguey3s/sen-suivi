import { ChangeDetectionStrategy, Component, model } from '@angular/core';

// Modale centrée sur desktop, feuille remontante sur mobile (ss-modal).
@Component({
  selector: 'ss-modal',
  standalone: true,
  template: `
    @if (ouverte()) {
      <div class="fond" (click)="ouverte.set(false)"></div>
      <div class="modale" role="dialog" aria-modal="true"><ng-content /></div>
    }
  `,
  styles: [
    `
      .fond {
        position: fixed;
        inset: 0;
        background: var(--ss-voile);
        z-index: 100;
      }
      .modale {
        position: fixed;
        z-index: 101;
        background: var(--ss-blanc);
        padding: var(--ss-espace-4) var(--ss-espace-3) var(--ss-espace-5);
        inset: auto 0 0 0;
        border-radius: var(--ss-rayon-grande-carte) var(--ss-rayon-grande-carte) 0 0;
        max-height: 90vh;
        overflow-y: auto;
      }
      @media (min-width: 900px) {
        .modale {
          inset: 50% auto auto 50%;
          transform: translate(-50%, -50%);
          width: 100%;
          max-width: 480px;
          border-radius: var(--ss-rayon-grande-carte);
          padding: var(--ss-espace-5);
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalComponent {
  readonly ouverte = model(false);
}
