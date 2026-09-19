import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_LIEU } from '../../core/config/images-lieux';
import { LieuDetente } from '../../core/models/suivi';
import { AuthService } from '../../core/services/auth.service';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { IconComponent } from '../../shared/icon/icon.component';

@Component({
  selector: 'ss-repertoire-lieux',
  standalone: true,
  imports: [RouterLink, IconComponent, CarteLieuxComponent],
  templateUrl: './repertoire.component.html',
  styleUrl: './repertoire.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RepertoireComponent {
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  protected readonly villeChoisie = signal<string | null>(null);
  protected readonly categorieChoisie = signal<string | null>(null);
  protected readonly recherche = signal('');
  protected readonly selection = signal<number | null>(null);
  protected readonly carteVisibleMobile = signal(false);

  private minuteur: ReturnType<typeof setTimeout> | undefined;

  private readonly tous = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, { defaultValue: [] });
  protected readonly villes = computed(() =>
    [...new Set(this.tous.value().map((l) => l.ville))].sort((a, b) => a.localeCompare(b, 'fr')),
  );
  protected readonly categories = computed(() =>
    [...new Set(this.tous.value().map((l) => l.categorie))].sort((a, b) => a.localeCompare(b, 'fr')),
  );

  // Filtres appliqués côté serveur : la requête repart à chaque changement
  protected readonly lieux = httpResource<LieuDetente[]>(
    () => {
      const params = new URLSearchParams();
      const v = this.villeChoisie();
      const c = this.categorieChoisie();
      const q = this.recherche().trim();
      if (v) params.set('ville', v);
      if (c) params.set('categorie', c);
      if (q) params.set('q', q);
      const chaine = params.toString();
      return `${API_BASE_URL}/lieux${chaine ? `?${chaine}` : ''}`;
    },
    { defaultValue: [] },
  );

  protected image(lieu: LieuDetente): string | null {
    return IMAGE_PAR_LIEU[lieu.nom] ?? null;
  }

  protected saisirRecherche(evenement: Event): void {
    const valeur = (evenement.target as HTMLInputElement).value;
    clearTimeout(this.minuteur);
    this.minuteur = setTimeout(() => this.recherche.set(valeur), 250);
  }

  protected basculerVille(ville: string | null): void {
    this.villeChoisie.set(ville);
    this.selection.set(null);
  }

  protected basculerCategorie(categorie: string): void {
    this.categorieChoisie.update((actuelle) => (actuelle === categorie ? null : categorie));
    this.selection.set(null);
  }

  protected ouvrir(id: number): void {
    void this.router.navigate(['/lieux', id]);
  }
}
