import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { FavorisService } from '../../core/services/favoris.service';
import { Ressource } from '../../core/models/suivi';
import {
  BlocContenu,
  ICONE_PAR_TYPE,
  LIBELLE_PAR_TYPE,
  ajouteLe,
  decouperContenu,
} from '../../core/utils/ressources';
import { CarteRessourceComponent } from '../../shared/carte-ressource/carte-ressource.component';
import { IconComponent } from '../../shared/icon/icon.component';

@Component({
  selector: 'ss-article',
  standalone: true,
  imports: [RouterLink, IconComponent, CarteRessourceComponent],
  templateUrl: './article.component.html',
  styleUrl: './article.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArticleComponent {
  private readonly favoris = inject(FavorisService);

  // Paramètre de route :id (withComponentInputBinding)
  readonly id = input.required<string>();

  protected readonly ressource = httpResource<Ressource>(() => `${API_BASE_URL}/ressources/${this.id()}`);
  private readonly toutes = httpResource<Ressource[]>(() => `${API_BASE_URL}/ressources`, {
    defaultValue: [],
  });

  protected readonly lienCopie = signal(false);

  protected readonly blocs = computed<BlocContenu[]>(() => {
    const r = this.ressource.value();
    return r ? decouperContenu(r.contenu) : [];
  });
  protected readonly sommaire = computed(() =>
    this.blocs().filter((b): b is Extract<BlocContenu, { genre: 'titre' }> => b.genre === 'titre'),
  );
  protected readonly introduction = computed(() => {
    const premier = this.blocs()[0];
    return premier?.genre === 'paragraphe' ? premier.texte : null;
  });
  protected readonly corps = computed(() =>
    this.introduction() ? this.blocs().slice(1) : this.blocs(),
  );

  protected readonly suggestions = computed(() => {
    const r = this.ressource.value();
    if (!r) return [];
    const autres = this.toutes.value().filter((x) => x.id !== r.id);
    const memeTheme = autres.filter((x) => x.thematique === r.thematique);
    return [...memeTheme, ...autres.filter((x) => x.thematique !== r.thematique)].slice(0, 3);
  });

  protected readonly typeLibelle = computed(() => {
    const r = this.ressource.value();
    return r ? LIBELLE_PAR_TYPE[r.type_ressource] : '';
  });
  protected readonly icone = computed(() => {
    const r = this.ressource.value();
    return r ? ICONE_PAR_TYPE[r.type_ressource] : 'article';
  });
  protected readonly ajout = computed(() => {
    const r = this.ressource.value();
    return r ? ajouteLe(r.date_publication) : '';
  });
  protected readonly estFavori = computed(() => this.favoris.estFavori(Number(this.id())));

  protected basculerFavori(): void {
    void this.favoris.basculer(Number(this.id()));
  }

  protected allerA(id: string): void {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  protected async partager(): Promise<void> {
    const url = window.location.href;
    const titre = this.ressource.value()?.titre ?? 'Sen Suivi';
    try {
      if (navigator.share) {
        await navigator.share({ title: titre, url });
      } else {
        await navigator.clipboard.writeText(url);
        this.lienCopie.set(true);
        setTimeout(() => this.lienCopie.set(false), 2500);
      }
    } catch {
      // partage annulé par l'utilisateur : rien à faire
    }
  }
}
