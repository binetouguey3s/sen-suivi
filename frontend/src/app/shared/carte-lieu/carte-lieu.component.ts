import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { imageDuLieu } from '../../core/config/images-lieux';
import { CATEGORIE_PAR_NOM } from '../../core/config/lieux';
import { LieuDetente } from '../../core/models/suivi';
import { CouvertureLieuComponent } from '../couverture-lieu/couverture-lieu.component';
import { IconComponent } from '../icon/icon.component';
import { PastilleAccesComponent } from '../pastille-acces/pastille-acces.component';

// Carte d'un lieu, partagée par le répertoire et « À découvrir aussi ».
@Component({
  selector: 'ss-carte-lieu',
  standalone: true,
  imports: [RouterLink, IconComponent, CouvertureLieuComponent, PastilleAccesComponent],
  templateUrl: './carte-lieu.component.html',
  styleUrl: './carte-lieu.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CarteLieuComponent {
  readonly lieu = input.required<LieuDetente>();
  readonly selectionne = input(false);
  readonly niveauTitre = input(2);

  protected readonly image = computed(() => imageDuLieu(this.lieu()));
  protected readonly icone = computed(() => CATEGORIE_PAR_NOM.get(this.lieu().categorie)?.icone ?? 'lieux');
}
