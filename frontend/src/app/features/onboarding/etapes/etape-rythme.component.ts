import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../../shared/interrupteur/interrupteur.component';
import { DUREES, FORMATS, FREQUENCES, MOMENTS } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 5 : moments, durée, formats préférés et rappels doux
@Component({
  selector: 'ss-etape-rythme',
  standalone: true,
  imports: [IconComponent, InterrupteurComponent],
  template: `
    <h1 class="ob-titre" tabindex="-1">Quand prendre soin de vous&nbsp;?</h1>
    <p class="ob-sous-titre">On s’adapte à votre rythme, pas l’inverse.</p>

    <section class="ob-section">
      <p class="ob-question" id="ob-moments">Vos moments préférés</p>
      <div class="ob-puces" role="group" aria-labelledby="ob-moments">
        @for (m of moments; track m.valeur) {
          @let choisi = store.moments().includes(m.valeur);
          <button type="button" class="ob-puce" [attr.aria-pressed]="choisi" (click)="store.basculer(store.moments, m.valeur)">
            @if (choisi) { <ss-icon nom="coche" taille="sm" /> }
            {{ m.libelle }}
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-duree">Le temps que vous pouvez y consacrer</p>
      <div class="durees" role="radiogroup" aria-labelledby="ob-duree">
        @for (d of durees; track d.valeur) {
          <button
            type="button"
            class="duree"
            role="radio"
            [attr.aria-checked]="store.duree() === d.valeur"
            (click)="store.duree.set(store.duree() === d.valeur ? null : d.valeur)"
          >
            <ss-icon nom="horloge" taille="sm" />
            <strong>{{ d.libelle }}</strong>
            <small>{{ d.aide }}</small>
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-formats">Vos formats préférés</p>
      <div class="ob-puces" role="group" aria-labelledby="ob-formats">
        @for (f of formats; track f.valeur) {
          @let choisi = store.formats().includes(f.valeur);
          <button type="button" class="ob-puce" [attr.aria-pressed]="choisi" (click)="store.basculer(store.formats, f.valeur)">
            @if (choisi) { <ss-icon nom="coche" taille="sm" /> }
            {{ f.libelle }}
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question">Rappels doux</p>
      <div class="ob-carte">
        <div class="ob-reglage">
          <span class="ob-reglage__icone"><ss-icon nom="cloche" taille="sm" /></span>
          <strong>Recevoir des rappels</strong>
          <ss-interrupteur libelle="Recevoir des rappels" [(actif)]="rappels" />
        </div>
        @if (store.rappels()) {
          <div class="segmente" role="radiogroup" aria-label="Fréquence des rappels">
            @for (f of frequences; track f.valeur) {
              <button
                type="button"
                role="radio"
                [attr.aria-checked]="store.frequenceRappels() === f.valeur"
                (click)="store.frequenceRappels.set(f.valeur)"
              >
                {{ f.libelle }}
              </button>
            }
          </div>
        }
      </div>
    </section>
  `,
  styleUrl: './etapes.scss',
  styles: `
    .durees {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .duree {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      padding: 12px 6px;
      border: 1.5px solid var(--ss-bordure);
      border-radius: 14px;
      background: var(--ss-surface);
      color: var(--ss-texte-marque);
      cursor: pointer;
    }
    .duree strong {
      margin-top: 4px;
      font-size: 14px;
      color: var(--ss-texte);
    }
    .duree small {
      font-size: 11px;
      color: var(--ss-texte-doux);
    }
    .duree[aria-checked='true'] {
      border-color: var(--ss-primaire);
      background: var(--ss-surface-legere);
      box-shadow: var(--ss-ombre);
    }
    .segmente {
      display: flex;
      gap: 4px;
      margin-top: 12px;
      padding: 4px;
      border-radius: 12px;
      background: var(--ss-surface-neutre);
    }
    .segmente button {
      flex: 1;
      min-height: 32px;
      border: none;
      border-radius: 9px;
      background: none;
      color: var(--ss-texte-doux);
      font-size: 12px;
      font-weight: var(--ss-poids-texte-fort);
      cursor: pointer;
    }
    .segmente [aria-checked='true'] {
      background: var(--ss-surface);
      color: var(--ss-texte);
      box-shadow: var(--ss-ombre);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeRythmeComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly moments = MOMENTS;
  protected readonly durees = DUREES;
  protected readonly formats = FORMATS;
  protected readonly frequences = FREQUENCES;
  protected readonly rappels = this.store.rappels;
}
