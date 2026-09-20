import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { PublicationForum, THEMATIQUES_FORUM, ThematiqueForum } from '../../core/models/forum';
import { ForumService } from '../../core/services/forum.service';
import { valeurs } from '../../core/utils/ressource';
import { depuisMaintenant } from '../../core/utils/temps';
import { BanniereForumComponent } from '../../shared/banniere-forum/banniere-forum.component';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalComponent } from '../../shared/modal/modal.component';

@Component({
  selector: 'ss-forum-liste',
  standalone: true,
  imports: [BanniereForumComponent, ChampComponent, IconComponent, ModalComponent],
  templateUrl: './liste.component.html',
  styleUrl: './liste.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ForumListeComponent {
  private readonly router = inject(Router);
  private readonly forumService = inject(ForumService);

  protected readonly thematiques = THEMATIQUES_FORUM;

  protected readonly thematiqueChoisie = signal<ThematiqueForum | null>(null);
  protected readonly recherche = signal('');
  private minuteur: ReturnType<typeof setTimeout> | undefined;

  protected readonly publications = httpResource<PublicationForum[]>(
    () => {
      const params = new URLSearchParams();
      const t = this.thematiqueChoisie();
      const q = this.recherche().trim();
      if (t) params.set('thematique', t);
      if (q) params.set('q', q);
      const chaine = params.toString();
      return `${API_BASE_URL}/forum/publications${chaine ? `?${chaine}` : ''}`;
    },
    { defaultValue: [] },
  );
  protected readonly liste = computed(() => valeurs(this.publications));

  protected readonly modaleOuverte = signal(false);
  protected readonly titre = signal('');
  protected readonly contenu = signal('');
  protected readonly thematiqueNouvelle = signal<ThematiqueForum | null>(null);
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);
  protected readonly confirmationOuverte = signal(false);

  protected saisirRecherche(evenement: Event): void {
    const valeur = (evenement.target as HTMLInputElement).value;
    clearTimeout(this.minuteur);
    this.minuteur = setTimeout(() => this.recherche.set(valeur), 250);
  }

  protected initiales(pseudonyme: string): string {
    return pseudonyme.slice(0, 2).toUpperCase();
  }

  protected depuis(iso: string): string {
    return depuisMaintenant(iso);
  }

  protected ouvrirPublication(id: number): void {
    void this.router.navigate(['/app/forum', id]);
  }

  protected ouvrirModale(): void {
    this.titre.set('');
    this.contenu.set('');
    this.thematiqueNouvelle.set(null);
    this.erreur.set(null);
    this.modaleOuverte.set(true);
  }

  protected async publier(): Promise<void> {
    if (!this.titre().trim() || !this.contenu().trim() || !this.thematiqueNouvelle()) {
      this.erreur.set('Merci de compléter le titre, le contenu et la thématique.');
      return;
    }
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      await this.forumService.publier(this.titre().trim(), this.contenu().trim(), this.thematiqueNouvelle()!);
      this.modaleOuverte.set(false);
      this.confirmationOuverte.set(true);
    } catch {
      this.erreur.set("L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }
}
