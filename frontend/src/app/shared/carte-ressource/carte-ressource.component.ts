import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { visuelRessource } from '../../core/config/illustrations-ressources';
import { Ressource } from '../../core/models/suivi';
import { FavorisService } from '../../core/services/favoris.service';
import { ICONE_PAR_TYPE, LIBELLE_PAR_TYPE, ajouteLe } from '../../core/utils/ressources';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'ss-carte-ressource',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './carte-ressource.component.html',
  styleUrl: './carte-ressource.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CarteRessourceComponent {
  private readonly favoris = inject(FavorisService);

  readonly ressource = input.required<Ressource>();
  readonly vedette = input(false);

  protected readonly icone = computed(() => ICONE_PAR_TYPE[this.ressource().type_ressource]);
  protected readonly format = computed(() => LIBELLE_PAR_TYPE[this.ressource().type_ressource]);
  protected readonly visuel = computed(() => visuelRessource(this.ressource().titre, this.ressource().thematique));
  protected readonly estFavori = computed(() => this.favoris.estFavori(this.ressource().id));
  protected readonly ajout = computed(() => ajouteLe(this.ressource().date_publication));

  protected basculerFavori(evenement: Event): void {
    evenement.preventDefault();
    evenement.stopPropagation();
    void this.favoris.basculer(this.ressource().id);
  }
}
