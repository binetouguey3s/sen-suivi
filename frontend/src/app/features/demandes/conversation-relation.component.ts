import { HttpErrorResponse, httpResource } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { AuthService } from '../../core/services/auth.service';
import { DemandesService, MessageRelation } from '../../core/services/demandes.service';
import { IconComponent } from '../../shared/icon/icon.component';

// Rafraîchissement du fil tant que la conversation est ouverte
const INTERVALLE_MS = 10_000;

interface DemandeResume {
  id: number;
  statut: string;
  professionnel_nom?: string;
  professionnel_specialite?: string;
  nom?: string | null;
  pseudonyme?: string;
}

// Messagerie privée entre un utilisateur et un professionnel, ouverte une
// fois la demande acceptée. Même écran pour les deux : /app/demandes/:id
// (utilisateur) et /pro/demandes/:id (professionnel).
@Component({
  selector: 'ss-conversation-relation',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './conversation-relation.component.html',
  styleUrl: './conversation-relation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConversationRelationComponent {
  private readonly service = inject(DemandesService);
  private readonly auth = inject(AuthService);

  readonly id = input.required<string>();

  protected readonly estProfessionnel = computed(() => this.auth.typeCompte() === 'professionnel');
  protected readonly retour = computed(() => (this.estProfessionnel() ? '/pro' : '/app/demandes'));

  private readonly demandes = httpResource<DemandeResume[]>(() => `${API_BASE_URL}/demandes-contact`);
  protected readonly demande = computed(() =>
    (this.demandes.hasValue() ? this.demandes.value() : []).find((d) => String(d.id) === this.id()),
  );
  protected readonly correspondant = computed(() => {
    const d = this.demande();
    return d ? (d.professionnel_nom ?? d.nom ?? d.pseudonyme ?? '') : '';
  });

  protected readonly messages = signal<MessageRelation[]>([]);
  protected readonly chargement = signal(true);
  protected readonly erreur = signal<string | null>(null);
  protected readonly brouillon = signal('');
  protected readonly envoiEnCours = signal(false);

  private readonly fil = viewChild<ElementRef<HTMLElement>>('fil');

  constructor() {
    afterNextRender(() => void this.charger());
    const minuterie = setInterval(() => void this.charger(), INTERVALLE_MS);
    inject(DestroyRef).onDestroy(() => clearInterval(minuterie));
  }

  private async charger(): Promise<void> {
    try {
      const recus = await this.service.messages(Number(this.id()));
      const nouveaux = recus.length !== this.messages().length;
      this.messages.set(recus);
      this.erreur.set(null);
      if (nouveaux) this.defilerEnBas();
    } catch (e) {
      this.erreur.set(
        e instanceof HttpErrorResponse && e.status === 403
          ? "La conversation s'ouvre quand le professionnel accepte la demande."
          : 'La conversation est momentanément indisponible.',
      );
    } finally {
      this.chargement.set(false);
    }
  }

  protected async envoyer(evenement: Event): Promise<void> {
    evenement.preventDefault();
    const contenu = this.brouillon().trim();
    if (!contenu || this.envoiEnCours()) return;
    this.envoiEnCours.set(true);
    try {
      const message = await this.service.envoyer(Number(this.id()), contenu);
      this.messages.update((liste) => [...liste, message]);
      this.brouillon.set('');
      this.defilerEnBas();
    } catch {
      this.erreur.set("L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }

  // Entrée envoie, Maj + Entrée passe à la ligne
  protected touche(evenement: KeyboardEvent): void {
    if (evenement.key === 'Enter' && !evenement.shiftKey) void this.envoyer(evenement);
  }

  protected heure(iso: string): string {
    const d = new Date(iso);
    const memeJour = d.toDateString() === new Date().toDateString();
    return memeJour
      ? d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }

  private defilerEnBas(): void {
    setTimeout(() => {
      const el = this.fil()?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
}
