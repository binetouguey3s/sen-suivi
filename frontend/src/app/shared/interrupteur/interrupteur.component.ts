import { ChangeDetectionStrategy, Component, input, model } from '@angular/core';

// Interrupteur accessible (role="switch"), utilisé dans les paramètres.
@Component({
  selector: 'ss-interrupteur',
  standalone: true,
  template: `
    <button
      type="button"
      role="switch"
      class="interrupteur"
      [class.interrupteur--actif]="actif()"
      [attr.aria-checked]="actif()"
      [attr.aria-label]="libelle()"
      (click)="actif.set(!actif())"
    >
      <span></span>
    </button>
  `,
  styles: [
    `
      .interrupteur {
        width: 44px;
        height: 24px;
        border: none;
        border-radius: var(--ss-rayon-pilule);
        background: var(--ss-gris-clair);
        padding: 2px;
        cursor: pointer;
        transition: background 0.15s ease;
        display: flex;
        align-items: center;
      }
      .interrupteur span {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--ss-blanc);
        box-shadow: var(--ss-ombre-carte);
        transition: transform 0.15s ease;
      }
      .interrupteur--actif {
        background: var(--ss-bleu-sen-suivi);
      }
      .interrupteur--actif span {
        transform: translateX(20px);
      }
      .interrupteur:focus-visible {
        outline: 2px solid var(--ss-bleu-sen-suivi);
        outline-offset: 2px;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InterrupteurComponent {
  readonly actif = model(false);
  readonly libelle = input.required<string>();
}
