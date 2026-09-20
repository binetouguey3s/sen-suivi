import { ChangeDetectionStrategy, Component } from '@angular/core';

import { IconComponent } from '../icon/icon.component';

// Bandeau rappelé en haut de chaque écran du forum (maquette « Espace d'échange »).
@Component({
  selector: 'ss-banniere-forum',
  standalone: true,
  imports: [IconComponent],
  template: `
    <p class="bf">
      <ss-icon nom="bouclier" taille="sm" /> Espace anonyme et modéré. Aucun conseil médical.
    </p>
  `,
  styles: [
    `
      .bf {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--ss-espace-1);
        margin: 0 0 var(--ss-espace-3);
        padding: var(--ss-espace-2);
        background: var(--ss-menthe-pale);
        color: var(--ss-bleu-profond);
        border-radius: var(--ss-rayon-champ);
        font-size: 14px;
        font-weight: var(--ss-poids-texte-fort);
        text-align: center;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BanniereForumComponent {}
