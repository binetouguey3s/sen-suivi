import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { MAX_PREOCCUPATIONS, PREOCCUPATIONS } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 3 : jusqu'à trois sujets qui occupent l'esprit en ce moment
@Component({
  selector: 'ss-etape-esprit',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="entete">
      <h1 class="ob-titre" tabindex="-1">Qu’est-ce qui occupe ton esprit&nbsp;?</h1>
      <span class="compteur" [class.compteur--plein]="store.maxAtteint()" aria-live="polite">
        @if (store.maxAtteint()) { <ss-icon nom="coche" taille="sm" /> }
        {{ store.preoccupations().length }}/{{ max }}
      </span>
    </div>
    <p class="ob-sous-titre">Choisis jusqu’à {{ max }} sujets. Tu pourras en changer quand tu veux.</p>

    <div class="ob-section ob-puces" role="group" aria-label="Sujets qui t'occupent l'esprit">
      @for (p of sujets; track p.valeur) {
        @let choisi = store.preoccupations().includes(p.valeur);
        <button
          type="button"
          class="ob-puce"
          [attr.aria-pressed]="choisi"
          [disabled]="!choisi && store.maxAtteint()"
          (click)="store.basculerPreoccupation(p.valeur)"
        >
          @if (choisi) { <ss-icon nom="coche" taille="sm" /> }
          {{ p.libelle }}
        </button>
      }
    </div>

    <button type="button" class="ob-option rien" [attr.aria-pressed]="store.rienDeParticulier()" (click)="store.basculerRien()">
      <span class="ob-option__icone"><ss-icon nom="coeur" taille="sm" /></span>
      Rien de particulier, je veux juste prendre soin de moi
    </button>

    @if (store.maxAtteint()) {
      <p class="ob-aide">Tu as atteint le maximum : désélectionne un sujet pour en choisir un autre.</p>
    }
  `,
  styleUrl: './etapes.scss',
  styles: `
    .entete {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    .compteur {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex: none;
      margin-top: 6px;
      padding: 3px 10px;
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-surface-neutre);
      color: var(--ss-texte-doux);
      font-size: 12px;
      font-weight: var(--ss-poids-titre);
    }
    .compteur--plein {
      background: var(--ss-surface-accent);
      color: var(--ss-texte-marque);
    }
    .ob-puce:not([aria-pressed='true']) {
      border-color: transparent;
      background: transparent;
      color: var(--ss-texte-doux);
    }
    .rien {
      margin-top: var(--ss-espace-3);
      border-style: dashed;
    }
    .rien[aria-pressed='true'] {
      border-style: solid;
      border-color: var(--ss-primaire);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeEspritComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly sujets = PREOCCUPATIONS;
  protected readonly max = MAX_PREOCCUPATIONS;
}
