import { HttpErrorResponse, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { PublicationForumDetail, THEMATIQUES_FORUM } from '../../core/models/forum';
import { Compte } from '../../core/services/compte.service';
import { ForumService } from '../../core/services/forum.service';
import { depuisMaintenant } from '../../core/utils/temps';
import { BanniereForumComponent } from '../../shared/banniere-forum/banniere-forum.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { SuiviModerationComponent } from '../../shared/suivi-moderation/suivi-moderation.component';

const LIBELLE_THEMATIQUE = Object.fromEntries(THEMATIQUES_FORUM.map((t) => [t.valeur, t.libelle]));

@Component({
  selector: 'ss-forum-detail',
  standalone: true,
  imports: [RouterLink, BanniereForumComponent, IconComponent, SuiviModerationComponent],
  templateUrl: './detail.component.html',
  styleUrl: './detail.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ForumDetailComponent {
  private readonly router = inject(Router);
  private readonly forumService = inject(ForumService);

  // Paramètre de route :id (withComponentInputBinding)
  readonly id = input.required<string>();

  protected readonly publication = httpResource<PublicationForumDetail>(
    () => `${API_BASE_URL}/forum/publications/${this.id()}`,
  );

  // Pseudonyme affiché au-dessus du champ de réponse
  protected readonly moi = httpResource<Compte>(() => `${API_BASE_URL}/comptes/moi`);

  protected readonly reponse = signal('');
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);
  // Réponse qu'on vient d'envoyer, suivie pendant sa modération
  protected readonly envoye = signal<number | null>(null);
  protected readonly publiee = signal(false);

  protected libelleThematique(valeur: string): string {
    return LIBELLE_THEMATIQUE[valeur] ?? valeur;
  }

  protected initiales(pseudonyme: string): string {
    return pseudonyme.slice(0, 2).toUpperCase();
  }

  protected depuis(iso: string): string {
    return depuisMaintenant(iso);
  }

  protected async envoyer(): Promise<void> {
    const texte = this.reponse().trim();
    if (!texte) return;
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      const envoi = await this.forumService.commenter(Number(this.id()), texte);
      this.reponse.set('');
      this.publiee.set(false);
      this.envoye.set(envoi.id);
    } catch (e) {
      const detail = e instanceof HttpErrorResponse && e.status === 403 ? e.error?.detail : null;
      this.erreur.set(detail ?? "L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }

  // Réponse publiée : on arrête le suivi (sinon chaque mise à jour le relancerait)
  // et on recharge la discussion pour l'afficher
  protected apresPublication(): void {
    this.envoye.set(null);
    this.publiee.set(true);
    this.publication.reload();
  }

  protected reformuler(contenu: string): void {
    this.envoye.set(null);
    this.reponse.set(contenu);
  }

  protected async retourAuForum(): Promise<void> {
    await this.router.navigateByUrl('/app/forum');
  }
}
