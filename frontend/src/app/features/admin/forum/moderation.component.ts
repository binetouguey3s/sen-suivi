import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';

import { API_BASE_URL } from '../../../core/config/api.config';
import {
  ActionModeration,
  CommentaireForumAdmin,
  DecisionIA,
  ElementFileModeration,
  PublicationForumAdmin,
  StatistiquesModeration,
  StatutModerationForum,
} from '../../../core/models/administration';
import { AdministrationService } from '../../../core/services/administration.service';
import { depuisMaintenant } from '../../../core/utils/temps';
import { valeurs } from '../../../core/utils/ressource';
import { PaginationComponent, tranche } from '../../../shared/pagination/pagination.component';

type Onglet = 'TOUS' | StatutModerationForum;
type Contenu = 'FILE' | 'PUBLICATIONS' | 'COMMENTAIRES';

const LIBELLE_STATUT: Record<StatutModerationForum, string> = {
  EN_ATTENTE: 'En attente',
  VISIBLE: 'Visible',
  MASQUE: 'Masqué',
  SUPPRIME: 'Supprimé',
  BLOQUE: 'Bloqué',
};

const LIBELLE_NIVEAU = { REGLES: 'règles', MODELE: 'modèle', REPLI: 'modèle indisponible' } as const;

@Component({
  selector: 'ss-admin-moderation-forum',
  standalone: true,
  imports: [PaginationComponent],
  templateUrl: './moderation.component.html',
  styleUrl: './moderation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminModerationForumComponent {
  private readonly administration = inject(AdministrationService);

  // La file de l'IA d'abord : c'est là que l'administrateur est attendu
  protected readonly contenu = signal<Contenu>('FILE');
  protected readonly onglet = signal<Onglet>('EN_ATTENTE');
  protected readonly selection = signal<Set<number>>(new Set());
  protected readonly enCours = signal<number | null>(null);
  protected readonly enCoursSelection = signal(false);
  protected readonly erreur = signal<string | null>(null);

  protected readonly onglets: { valeur: Onglet; libelle: string }[] = [
    { valeur: 'TOUS', libelle: 'Tous' },
    { valeur: 'EN_ATTENTE', libelle: 'En attente' },
    { valeur: 'VISIBLE', libelle: 'Visibles' },
    { valeur: 'BLOQUE', libelle: 'Bloqués' },
    { valeur: 'MASQUE', libelle: 'Masqués' },
    { valeur: 'SUPPRIME', libelle: 'Supprimés' },
  ];

  private readonly url = computed(() => {
    const base =
      this.contenu() === 'PUBLICATIONS'
        ? `${API_BASE_URL}/forum/moderation/publications`
        : `${API_BASE_URL}/forum/moderation/commentaires`;
    const o = this.onglet();
    return o === 'TOUS' ? base : `${base}?statut=${o}`;
  });

  protected readonly publications = httpResource<PublicationForumAdmin[]>(
    () => (this.contenu() === 'PUBLICATIONS' ? this.url() : undefined),
    { defaultValue: [] },
  );
  protected readonly commentaires = httpResource<CommentaireForumAdmin[]>(
    () => (this.contenu() === 'COMMENTAIRES' ? this.url() : undefined),
    { defaultValue: [] },
  );

  protected readonly file = httpResource<ElementFileModeration[]>(
    () => (this.contenu() === 'FILE' ? `${API_BASE_URL}/forum/moderation/file` : undefined),
    { defaultValue: [] },
  );
  protected readonly statistiques = httpResource<StatistiquesModeration>(() => `${API_BASE_URL}/forum/moderation/statistiques`);
  protected readonly listeFile = computed(() => valeurs(this.file));

  protected readonly listePublications = computed(() => valeurs(this.publications));
  protected readonly listeCommentaires = computed(() => valeurs(this.commentaires));

  // Pagination : retour à la première page quand les filtres changent
  protected readonly page = linkedSignal({ source: () => [this.contenu(), this.onglet()], computation: () => 1 });
  protected readonly listeFilePage = computed(() => tranche(this.listeFile(), this.page(), 15));
  protected readonly listePublicationsPage = computed(() => tranche(this.listePublications(), this.page(), 20));
  protected readonly listeCommentairesPage = computed(() => tranche(this.listeCommentaires(), this.page(), 20));
  private readonly ressourceActive = computed(() =>
    this.contenu() === 'FILE' ? this.file : this.contenu() === 'PUBLICATIONS' ? this.publications : this.commentaires,
  );
  protected readonly enChargement = computed(() => this.ressourceActive().isLoading());
  protected readonly enErreur = computed(() => !!this.ressourceActive().error());
  protected readonly nombreSelectionnes = computed(() => this.selection().size);

  protected libelle(statut: StatutModerationForum): string {
    return LIBELLE_STATUT[statut];
  }

  protected niveau(n: DecisionIA['niveau']): string {
    return LIBELLE_NIVEAU[n] ?? n;
  }

  protected depuis(iso: string): string {
    return depuisMaintenant(iso);
  }

  protected changerContenu(c: Contenu): void {
    this.contenu.set(c);
    this.selection.set(new Set());
  }

  protected changerOnglet(o: Onglet): void {
    this.onglet.set(o);
    this.selection.set(new Set());
  }

  protected basculerSelection(id: number): void {
    const actuelle = new Set(this.selection());
    actuelle.has(id) ? actuelle.delete(id) : actuelle.add(id);
    this.selection.set(actuelle);
  }

  protected toutSelectionner(coche: boolean): void {
    const ids = this.contenu() === 'PUBLICATIONS' ? this.listePublications().map((p) => p.id) : this.listeCommentaires().map((c) => c.id);
    this.selection.set(coche ? new Set(ids) : new Set());
  }

  private recharger(): void {
    this.ressourceActive().reload();
    this.statistiques.reload();
  }

  // Décision humaine sur un élément de la file, en un clic
  protected async trancher(element: ElementFileModeration, action: ActionModeration): Promise<void> {
    this.enCours.set(element.id);
    this.erreur.set(null);
    try {
      await this.administration.trancher(element.id, action);
      this.recharger();
    } catch {
      this.erreur.set("L'action a échoué. Réessayez dans un instant.");
    } finally {
      this.enCours.set(null);
    }
  }

  private async agirSur(id: number, statut: StatutModerationForum): Promise<void> {
    if (this.contenu() === 'PUBLICATIONS') {
      await this.administration.modererPublication(id, statut);
    } else {
      await this.administration.modererCommentaire(id, statut);
    }
  }

  protected async agir(id: number, statut: StatutModerationForum): Promise<void> {
    this.enCours.set(id);
    this.erreur.set(null);
    try {
      await this.agirSur(id, statut);
      this.recharger();
    } catch {
      this.erreur.set("L'action a échoué. Réessayez dans un instant.");
    } finally {
      this.enCours.set(null);
    }
  }

  protected async agirSurSelection(statut: StatutModerationForum): Promise<void> {
    this.enCoursSelection.set(true);
    this.erreur.set(null);
    try {
      await Promise.all([...this.selection()].map((id) => this.agirSur(id, statut)));
      this.selection.set(new Set());
      this.recharger();
    } catch {
      this.erreur.set("L'action a échoué pour au moins un élément. Réessayez dans un instant.");
    } finally {
      this.enCoursSelection.set(false);
    }
  }
}
