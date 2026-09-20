import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, input, linkedSignal, signal } from '@angular/core';

import { API_BASE_URL } from '../../core/config/api.config';
import { Ressource } from '../../core/models/suivi';
import { ICONE_PAR_TYPE, LIBELLE_PAR_TYPE } from '../../core/utils/ressources';
import { CarteRessourceComponent } from '../../shared/carte-ressource/carte-ressource.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { valeurs } from '../../core/utils/ressource';

type Format = Ressource['type_ressource'];
const FORMATS: Format[] = ['ARTICLE', 'EXERCICE', 'PODCAST'];
const PAGE = 5;

@Component({
  selector: 'ss-bibliotheque',
  standalone: true,
  imports: [CarteRessourceComponent, IconComponent],
  templateUrl: './bibliotheque.component.html',
  styleUrl: './bibliotheque.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BibliothequeComponent {
  // Paramètres d'URL (?format=…&thematique=…) liés aux entrées du composant
  readonly format = input<string>();
  readonly thematique = input<string>();

  protected readonly formats = FORMATS.map((valeur) => ({
    valeur,
    libelle: LIBELLE_PAR_TYPE[valeur],
    icone: ICONE_PAR_TYPE[valeur],
  }));

  protected readonly formatChoisi = linkedSignal<Format | null>(() => {
    const f = this.format();
    return FORMATS.includes(f as Format) ? (f as Format) : null;
  });
  protected readonly thematiqueChoisie = linkedSignal<string | null>(() => this.thematique() ?? null);
  protected readonly recherche = signal('');
  protected readonly limite = signal(PAGE);

  private minuteur: ReturnType<typeof setTimeout> | undefined;

  // Toutes les ressources : sert uniquement à construire la liste des thématiques
  private readonly toutes = httpResource<Ressource[]>(() => `${API_BASE_URL}/ressources`, {
    defaultValue: [],
  });
  protected readonly thematiques = computed(() =>
    [...new Set(valeurs(this.toutes).map((r) => r.thematique))].sort((a, b) => a.localeCompare(b, 'fr')),
  );

  // Ressources filtrées côté serveur : la requête repart à chaque changement de filtre
  protected readonly ressources = httpResource<Ressource[]>(
    () => {
      const params = new URLSearchParams();
      const f = this.formatChoisi();
      const t = this.thematiqueChoisie();
      const q = this.recherche().trim();
      if (f) params.set('format', f);
      if (t) params.set('thematique', t);
      if (q) params.set('q', q);
      const chaine = params.toString();
      return `${API_BASE_URL}/ressources${chaine ? `?${chaine}` : ''}`;
    },
    { defaultValue: [] },
  );

  protected readonly visibles = computed(() => valeurs(this.ressources).slice(0, this.limite()));
  protected readonly resteAVoir = computed(() => valeurs(this.ressources).length > this.limite());

  protected saisirRecherche(evenement: Event): void {
    const valeur = (evenement.target as HTMLInputElement).value;
    clearTimeout(this.minuteur);
    this.minuteur = setTimeout(() => {
      this.recherche.set(valeur);
      this.limite.set(PAGE);
    }, 250);
  }

  protected choisirThematique(valeur: string | null): void {
    this.thematiqueChoisie.set(valeur);
    this.limite.set(PAGE);
  }

  protected choisirFormat(valeur: Format): void {
    this.formatChoisi.update((actuel) => (actuel === valeur ? null : valeur));
    this.limite.set(PAGE);
  }

  protected voirPlus(): void {
    this.limite.set(valeurs(this.ressources).length);
  }
}
