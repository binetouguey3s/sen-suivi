import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { OnboardingStore } from '../onboarding.store';

// Présentation : ce que l'on va demander, et pourquoi
@Component({
  selector: 'ss-etape-intro',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="intro">
      <h1 class="ob-titre" tabindex="-1">Faisons connaissance</h1>
      <p class="ob-sous-titre">
        En 2 minutes, je découvre ce qui te fait du bien pour te proposer des ressources, des activités et des
        professionnels qui te ressemblent.
      </p>
      <ul class="intro__atouts">
        <li><ss-icon nom="horloge" taille="sm" /> 2 minutes</li>
        <li><ss-icon nom="cadenas" taille="sm" /> Confidentiel</li>
        <li><ss-icon nom="ecrire" taille="sm" /> Modifiable</li>
      </ul>

      @if (store.pourquoiOuvert()) {
        <div id="pourquoi" class="ob-carte intro__pourquoi">
          <ss-icon nom="info" taille="sm" />
          <p>
            Tes réponses servent uniquement à adapter le ton de Titou et les contenus proposés. Toutes les questions
            sont facultatives, et tu peux tout modifier ou supprimer depuis ton profil. Ce n’est pas un diagnostic.
          </p>
        </div>
      }
    </div>
  `,
  styleUrl: './etapes.scss',
  styles: `
    .intro {
      text-align: center;
    }
    .intro__atouts {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 8px;
      margin: 16px 0 0;
      padding: 0;
      list-style: none;
    }
    .intro__atouts li {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border: 1px solid var(--ss-bordure);
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-surface);
      font-size: 12px;
      font-weight: var(--ss-poids-texte-fort);
    }
    .intro__pourquoi {
      display: flex;
      gap: 10px;
      margin-top: 16px;
      text-align: left;
      color: var(--ss-texte-marque);
    }
    .intro__pourquoi p {
      margin: 0;
      font-size: 13px;
      color: var(--ss-texte);
    }
    @media (min-width: 900px) {
      .intro {
        text-align: left;
      }
      .intro__atouts {
        justify-content: flex-start;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeIntroComponent {
  protected readonly store = inject(OnboardingStore);
}
