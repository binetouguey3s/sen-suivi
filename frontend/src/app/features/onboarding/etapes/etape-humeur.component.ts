import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { HUMEURS, SOMMEILS } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 2 : humeur du moment, énergie et sommeil. Point de départ du journal, pas un diagnostic.
@Component({
  selector: 'ss-etape-humeur',
  standalone: true,
  imports: [IconComponent],
  template: `
    <h1 class="ob-titre" tabindex="-1">Comment te sens-tu en ce moment&nbsp;?</h1>
    <p class="ob-sous-titre">Il n’y a pas de bonne ou de mauvaise réponse.</p>

    <section class="ob-section ob-carte humeurs" role="radiogroup" aria-label="Ton humeur">
      @for (h of humeurs; track h.valeur) {
        <button
          type="button"
          class="humeur"
          role="radio"
          [attr.aria-checked]="store.humeur() === h.note"
          (click)="store.humeur.set(store.humeur() === h.note ? null : h.note)"
        >
          <span class="humeur__visage humeur__visage--{{ h.note }}"><ss-icon [nom]="h.icone!" [taille]="store.humeur() === h.note ? 'lg' : 'md'" /></span>
          <span class="humeur__libelle">{{ h.libelle }}</span>
        </button>
      }
    </section>

    <section class="ob-section">
      <label class="ob-question" for="ob-energie">Ton énergie ces derniers jours</label>
      <input
        id="ob-energie"
        class="energie"
        type="range"
        min="0"
        max="100"
        step="5"
        [value]="store.energie()"
        [style.--remplissage]="store.energie() + '%'"
        [attr.aria-valuetext]="niveauEnergie()"
        (input)="store.energie.set(+$any($event.target).value)"
      />
      <div class="energie__reperes" aria-hidden="true">
        <span>Épuisé·e</span><span>Moyenne</span><span>En forme</span>
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-sommeil">Ton sommeil cette semaine</p>
      <div class="ob-options" role="radiogroup" aria-labelledby="ob-sommeil">
        @for (s of sommeils; track s.valeur) {
          <button
            type="button"
            class="ob-option"
            role="radio"
            [attr.aria-checked]="store.sommeil() === s.valeur"
            (click)="store.sommeil.set(store.sommeil() === s.valeur ? null : s.valeur)"
          >
            <span class="ob-option__icone"><ss-icon [nom]="s.icone!" taille="sm" /></span>
            {{ s.libelle }}
            <span class="ob-option__radio" aria-hidden="true"></span>
          </button>
        }
      </div>
    </section>

    <p class="ob-note">
      <ss-icon nom="info" taille="sm" />
      Ce n’est pas un diagnostic, juste le point de départ de ton journal d’humeur.
    </p>
  `,
  styleUrl: './etapes.scss',
  styles: `
    .humeurs {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 4px;
    }
    .humeur {
      display: flex;
      flex: 1;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      padding: 0;
      border: none;
      background: none;
      color: var(--ss-texte-doux);
      cursor: pointer;
    }
    .humeur__visage {
      display: grid;
      place-items: center;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--ss-surface-neutre);
      color: var(--ss-texte-marque);
      transition:
        width 0.2s var(--ss-ease),
        height 0.2s var(--ss-ease);
    }
    .humeur__visage--4,
    .humeur__visage--5 {
      background: var(--ss-surface-accent);
    }
    .humeur__libelle {
      font-size: 11px;
    }
    .humeur[aria-checked='true'] .humeur__visage {
      width: 52px;
      height: 52px;
      background: var(--ss-surface-accent);
      box-shadow: 0 0 0 2px var(--ss-primaire);
    }
    .humeur[aria-checked='true'] .humeur__libelle {
      color: var(--ss-texte);
      font-weight: var(--ss-poids-titre);
    }
    .energie {
      width: 100%;
      height: 6px;
      margin: 8px 0;
      border-radius: var(--ss-rayon-pilule);
      background: linear-gradient(90deg, var(--ss-accent) var(--remplissage), var(--ss-bordure) var(--remplissage));
      appearance: none;
      cursor: pointer;
    }
    .energie::-webkit-slider-thumb {
      appearance: none;
      width: 20px;
      height: 20px;
      border: 3px solid var(--ss-primaire);
      border-radius: 50%;
      background: var(--ss-surface);
      box-shadow: var(--ss-ombre);
    }
    .energie::-moz-range-thumb {
      width: 16px;
      height: 16px;
      border: 3px solid var(--ss-primaire);
      border-radius: 50%;
      background: var(--ss-surface);
    }
    .energie__reperes {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--ss-texte-doux);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeHumeurComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly humeurs = HUMEURS;
  protected readonly sommeils = SOMMEILS;

  protected readonly niveauEnergie = computed(() => {
    const e = this.store.energie();
    return e < 34 ? 'Épuisé·e' : e < 67 ? 'Moyenne' : 'En forme';
  });
}
