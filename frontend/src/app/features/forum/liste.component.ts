import { HttpErrorResponse, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { Router } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { PublicationForum, THEMATIQUES_FORUM, ThematiqueForum } from '../../core/models/forum';
import { ForumService, MesMessagesForum } from '../../core/services/forum.service';
import { valeurs } from '../../core/utils/ressource';
import { depuisMaintenant } from '../../core/utils/temps';
import { BanniereForumComponent } from '../../shared/banniere-forum/banniere-forum.component';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalComponent } from '../../shared/modal/modal.component';
import { SuiviModerationComponent } from '../../shared/suivi-moderation/suivi-moderation.component';
import { PaginationComponent, tranche } from '../../shared/pagination/pagination.component';

@Component({
  selector: 'ss-forum-liste',
  standalone: true,
  imports: [BanniereForumComponent, ChampComponent, IconComponent, ModalComponent, SuiviModerationComponent, PaginationComponent],
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

  // Pagination : retour à la première page quand les filtres changent
  protected readonly page = linkedSignal({ source: () => [this.thematiqueChoisie(), this.recherche()], computation: () => 1 });
  protected readonly listePage = computed(() => tranche(this.liste(), this.page(), 10));

  protected readonly modaleOuverte = signal(false);
  protected readonly titre = signal('');
  protected readonly contenu = signal('');
  protected readonly thematiqueNouvelle = signal<ThematiqueForum | null>(null);
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);
  protected readonly confirmationOuverte = signal(false);
  // Publication qu'on vient d'envoyer, suivie pendant sa modération
  protected readonly envoyee = signal<number | null>(null);

  // Messages de l'auteur pas (encore) publiés, et suspension éventuelle
  protected readonly mesMessages = httpResource<MesMessagesForum>(() => `${API_BASE_URL}/forum/mes-messages`);
  protected readonly nonPublies = computed(() =>
    (this.mesMessages.hasValue() ? this.mesMessages.value().messages : []).filter(
      (m) => m.statut_moderation === 'BLOQUE' || m.statut_moderation === 'EN_ATTENTE',
    ),
  );
  protected readonly suspenduJusquAu = computed(() =>
    this.mesMessages.hasValue() && this.mesMessages.value().suspendu_jusqu_au
      ? new Date(this.mesMessages.value().suspendu_jusqu_au!).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
      : null,
  );

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

  // Message non publié : on rouvre la saisie avec le texte, pour le reformuler
  protected reformuler(contenu: string): void {
    this.confirmationOuverte.set(false);
    this.contenu.set(contenu);
    this.erreur.set(null);
    this.modaleOuverte.set(true);
  }

  protected apresPublication(): void {
    this.publications.reload();
    this.mesMessages.reload();
  }

  protected async publier(): Promise<void> {
    if (!this.titre().trim() || !this.contenu().trim() || !this.thematiqueNouvelle()) {
      this.erreur.set('Merci de compléter le titre, le contenu et la thématique.');
      return;
    }
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      const envoi = await this.forumService.publier(this.titre().trim(), this.contenu().trim(), this.thematiqueNouvelle()!);
      this.envoyee.set(envoi.id);
      this.modaleOuverte.set(false);
      this.confirmationOuverte.set(true);
    } catch (e) {
      const detail = e instanceof HttpErrorResponse && e.status === 403 ? e.error?.detail : null;
      this.erreur.set(detail ?? "L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }
}
