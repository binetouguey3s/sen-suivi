import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';

import { visuelRessource } from '../../core/config/illustrations-ressources';
import { Ressource } from '../../core/models/suivi';
import { FavorisService } from '../../core/services/favoris.service';
import { ICONE_PAR_TYPE, LIBELLE_PAR_TYPE, ajouteLe } from '../../core/utils/ressources';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'ss-carte-ressource',
  standalone: true,
  imports: [NgTemplateOutlet, RouterLink, IconComponent],
  templateUrl: './carte-ressource.component.html',
  styleUrl: './carte-ressource.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CarteRessourceComponent {
  private readonly favoris = inject(FavorisService);

  readonly ressource = input.required<Ressource>();
  readonly vedette = input(false);
  // Aperçu dans l'éditeur du professionnel : ni lien, ni favori
  readonly apercu = input(false);
  // Chapô (premier paragraphe) sous le titre, sur 3 lignes au plus
  readonly avecChapo = input(false);

  protected readonly icone = computed(() => ICONE_PAR_TYPE[this.ressource().type_ressource]);
  protected readonly format = computed(() => LIBELLE_PAR_TYPE[this.ressource().type_ressource]);
  protected readonly visuel = computed(() => visuelRessource(this.ressource().titre, this.ressource().thematique));
  protected readonly estFavori = computed(() => this.favoris.estFavori(this.ressource().id));
  protected readonly ajout = computed(() => ajouteLe(this.ressource().date_publication));
  protected readonly estPodcast = computed(() => this.ressource().type_ressource === 'PODCAST');
  protected readonly chapo = computed(() => this.ressource().contenu.trim().split(/\n\s*\n/)[0]?.replace(/^#+\s*|^>\s*/, '') ?? '');

  protected initiales(nom: string): string {
    return nom
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((mot) => mot[0].toUpperCase())
      .join('');
  }

  protected basculerFavori(evenement: Event): void {
    evenement.preventDefault();
    evenement.stopPropagation();
    void this.favoris.basculer(this.ressource().id);
  }
}
