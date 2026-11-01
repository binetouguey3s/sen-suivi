import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { CATEGORIE_PAR_NOM } from '../../core/config/lieux';
import { IconComponent } from '../icon/icon.component';

// Couverture illustrée d'un lieu sans photo : dégradé et icône de sa catégorie,
// jamais une fausse photo. Décorative : le nom du lieu est écrit à côté.
@Component({
  selector: 'ss-couverture-lieu',
  standalone: true,
  imports: [IconComponent],
  template: `<ss-icon [nom]="categorie()?.icone ?? 'lieux'" taille="xl" />`,
  host: { 'aria-hidden': 'true', '[class]': "'couverture--' + (categorie()?.famille ?? 'vert')" },
  styles: `
    :host {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      color: var(--ss-texte-sur-photo);
    }
    :host(.couverture--eau) { background: linear-gradient(135deg, var(--ss-couv-eau-debut), var(--ss-couv-eau-fin)); }
    :host(.couverture--vert) { background: linear-gradient(135deg, var(--ss-couv-vert-debut), var(--ss-couv-vert-fin)); }
    :host(.couverture--sable) { background: linear-gradient(135deg, var(--ss-couv-sable-debut), var(--ss-couv-sable-fin)); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CouvertureLieuComponent {
  readonly nomCategorie = input.required<string>();
  protected readonly categorie = computed(() => CATEGORIE_PAR_NOM.get(this.nomCategorie()));
}
