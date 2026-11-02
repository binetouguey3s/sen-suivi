import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { ACCES_PAR_CODE } from '../../core/config/lieux';
import { AccesLieu } from '../../core/models/suivi';
import { IconComponent } from '../icon/icon.component';

// Accès d'un lieu : l'icône et le libellé disent la même chose que la couleur.
@Component({
  selector: 'ss-pastille-acces',
  standalone: true,
  imports: [IconComponent],
  template: `
    <span [class]="'pastille-acces pastille-acces--' + acces()" [class.pastille-acces--sur-photo]="surPhoto()">
      <ss-icon [nom]="detail()!.icone" taille="sm" /> {{ detail()!.libelle }}
    </span>
  `,
  styles: `
    .pastille-acces {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: var(--ss-rayon-pilule);
      padding: 4px 10px;
      font-size: var(--ss-texte-taille-min);
      font-weight: var(--ss-poids-texte-fort);
      white-space: nowrap;
      backdrop-filter: blur(8px);
    }
    .pastille-acces--GRATUIT { color: var(--ss-acces-gratuit); background: var(--ss-acces-gratuit-fond); }
    .pastille-acces--LIBRE { color: var(--ss-acces-libre); background: var(--ss-acces-libre-fond); }
    .pastille-acces--PAYANT { color: var(--ss-acces-payant); background: var(--ss-acces-payant-fond); }
    .pastille-acces--MIXTE { color: var(--ss-acces-mixte); background: var(--ss-acces-mixte-fond); }
    .pastille-acces--RESTREINT { color: var(--ss-acces-restreint); background: var(--ss-acces-restreint-fond); }
    /* Sur une photo : fond sombre flouté dans les deux thèmes, teintes claires */
    .pastille-acces--sur-photo {
      box-sizing: border-box;
      min-height: 28px;
      background: var(--ss-photo-voile);
      backdrop-filter: blur(8px);
    }
    .pastille-acces--GRATUIT.pastille-acces--sur-photo { color: var(--ss-acces-gratuit-sur-photo); }
    .pastille-acces--LIBRE.pastille-acces--sur-photo { color: var(--ss-acces-libre-sur-photo); }
    .pastille-acces--PAYANT.pastille-acces--sur-photo { color: var(--ss-acces-payant-sur-photo); }
    .pastille-acces--MIXTE.pastille-acces--sur-photo { color: var(--ss-acces-mixte-sur-photo); }
    .pastille-acces--RESTREINT.pastille-acces--sur-photo { color: var(--ss-acces-restreint-sur-photo); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PastilleAccesComponent {
  readonly acces = input.required<AccesLieu>();
  readonly surPhoto = input(false);
  protected readonly detail = computed(() => ACCES_PAR_CODE.get(this.acces()));
}
