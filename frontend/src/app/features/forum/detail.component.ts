import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { PublicationForumDetail, THEMATIQUES_FORUM } from '../../core/models/forum';
import { Compte } from '../../core/services/compte.service';
import { ForumService } from '../../core/services/forum.service';
import { depuisMaintenant } from '../../core/utils/temps';
import { BanniereForumComponent } from '../../shared/banniere-forum/banniere-forum.component';
import { IconComponent } from '../../shared/icon/icon.component';

const LIBELLE_THEMATIQUE = Object.fromEntries(THEMATIQUES_FORUM.map((t) => [t.valeur, t.libelle]));

@Component({
  selector: 'ss-forum-detail',
  standalone: true,
  imports: [RouterLink, BanniereForumComponent, IconComponent],
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
  protected readonly envoye = signal(false);

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
      await this.forumService.commenter(Number(this.id()), texte);
      this.reponse.set('');
      this.envoye.set(true);
    } catch {
      this.erreur.set("L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }

  protected async retourAuForum(): Promise<void> {
    await this.router.navigateByUrl('/app/forum');
  }
}
