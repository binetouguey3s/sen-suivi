import { ChangeDetectionStrategy, Component } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';

// Écran d'accueil visuel : la promesse de Sen Suivi avant les questions
@Component({
  selector: 'ss-etape-splash',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="splash">
      <img class="splash__logo" src="/logo-sen-suivi.png" alt="" />
      <h1 class="ob-titre splash__titre" tabindex="-1">Un esprit sain pour une société saine</h1>
      <p class="ob-sous-titre splash__texte">
        Sen Suivi t’aide à prendre soin de ton bien-être au quotidien : respirer, écouter, écrire, et te faire
        accompagner quand tu en as besoin.
      </p>
      <ul class="splash__atouts">
        <li><ss-icon nom="cadenas" taille="sm" /> Confidentiel</li>
        <li><ss-icon nom="horloge" taille="sm" /> À ton rythme</li>
        <li><ss-icon nom="globe" taille="sm" /> Français et wolof</li>
      </ul>
    </div>
  `,
  styleUrl: './etapes.scss',
  styles: `
    .splash {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }
    .splash__logo {
      width: 84px;
      height: 84px;
      margin-bottom: 8px;
      object-fit: contain;
      filter: var(--ss-logo-filtre);
    }
    .splash__marque {
      margin: 4px 0 6px;
      font-family: var(--ss-police-titres);
      font-size: 13px;
      font-weight: var(--ss-poids-titre-fort);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--ss-texte-marque);
    }
    .splash__titre {
      font-size: 20px;
      font-weight: var(--ss-poids-titre);
    }
    .splash__texte,
    .splash__atouts {
      display: none;
    }
    .splash__atouts {
      gap: 8px;
      flex-wrap: wrap;
      margin: 18px 0 0;
      padding: 0;
      list-style: none;
    }
    .splash__atouts li {
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
    @media (min-width: 900px) {
      .splash {
        align-items: flex-start;
        text-align: left;
      }
      .splash__marque {
        display: none;
      }
      .splash__titre {
        font-size: 40px;
        font-weight: var(--ss-poids-titre-fort);
        letter-spacing: var(--ss-interlettrage-grand);
      }
      .splash__texte {
        display: block;
        margin-top: 8px;
        font-size: 15px;
      }
      .splash__atouts {
        display: flex;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeSplashComponent {}
