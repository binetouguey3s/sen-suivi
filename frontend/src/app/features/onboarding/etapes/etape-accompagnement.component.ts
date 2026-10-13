import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../../shared/interrupteur/interrupteur.component';
import { AISANCES, ECHANGES_PRO, METIERS } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 6 : envie d'être accompagné, et consentements sur les données
@Component({
  selector: 'ss-etape-accompagnement',
  standalone: true,
  imports: [IconComponent, InterrupteurComponent],
  template: `
    <h1 class="ob-titre" tabindex="-1">Accompagnement et confidentialité</h1>
    <p class="ob-sous-titre">Tu gardes la main sur tes données, à tout moment.</p>

    <section class="ob-section">
      <p class="ob-question" id="ob-echange">Échanger avec un professionnel, un jour&nbsp;?</p>
      <div class="ob-options" role="radiogroup" aria-labelledby="ob-echange">
        @for (e of echanges; track e.valeur) {
          <button
            type="button"
            class="ob-option"
            role="radio"
            [attr.aria-checked]="store.echangePro() === e.valeur"
            (click)="store.echangePro.set(store.echangePro() === e.valeur ? null : e.valeur)"
          >
            <span class="ob-option__icone"><ss-icon [nom]="e.icone!" taille="sm" /></span>
            {{ e.libelle }}
            <span class="ob-option__radio" aria-hidden="true"></span>
          </button>
        }
      </div>
    </section>

    @if (store.echangePro() !== 'pas_maintenant') {
      <section class="ob-section">
        <p class="ob-question" id="ob-metiers">Quel accompagnement t’intéresserait&nbsp;?</p>
        <div class="ob-puces" role="group" aria-labelledby="ob-metiers">
          @for (m of metiers; track m.valeur) {
            @let choisi = store.metiers().includes(m.valeur);
            <button type="button" class="ob-puce" [attr.aria-pressed]="choisi" (click)="store.basculer(store.metiers, m.valeur)">
              @if (choisi) { <ss-icon nom="coche" taille="sm" /> }
              {{ m.libelle }}
            </button>
          }
        </div>
      </section>

      <section class="ob-section">
        <p class="ob-question" id="ob-aise">Je serais plus à l’aise avec</p>
        <div class="ob-puces" role="radiogroup" aria-labelledby="ob-aise">
          @for (a of aisances; track a.valeur) {
            <button
              type="button"
              class="ob-puce"
              role="radio"
              [attr.aria-checked]="store.aiseAvec() === a.valeur"
              (click)="store.aiseAvec.set(store.aiseAvec() === a.valeur ? null : a.valeur)"
            >
              @if (store.aiseAvec() === a.valeur) { <ss-icon nom="coche" taille="sm" /> }
              {{ a.libelle }}
            </button>
          }
        </div>
      </section>
    }

    <section class="ob-section">
      <p class="ob-question">Tes données, tes choix</p>
      <div class="ob-carte">
        <div class="ob-reglage">
          <span class="ob-reglage__icone"><ss-icon nom="suggestion" taille="sm" /></span>
          <span>
            <strong>Personnaliser mes suggestions</strong>
            <small>Utiliser mes réponses pour choisir mes ressources et adapter Titou.</small>
          </span>
          <ss-interrupteur libelle="Personnaliser mes suggestions" [(actif)]="personnalisation" />
        </div>
        <div class="ob-reglage">
          <span class="ob-reglage__icone"><ss-icon nom="chat" taille="sm" /></span>
          <span>
            <strong>Conserver mes échanges avec Titou</strong>
            <small>Désactivé : rien n’est gardé après la conversation.</small>
          </span>
          <ss-interrupteur libelle="Conserver mes échanges avec Titou" [(actif)]="conserver" />
        </div>
      </div>
      <p class="ob-note">
        <ss-icon nom="cadenas" taille="sm" />
        Tout est modifiable ou supprimable depuis ton profil.
      </p>
    </section>
  `,
  styleUrl: './etapes.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeAccompagnementComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly echanges = ECHANGES_PRO;
  protected readonly metiers = METIERS;
  protected readonly aisances = AISANCES;
  protected readonly personnalisation = this.store.personnalisation;
  protected readonly conserver = this.store.conserverEchanges;
}
