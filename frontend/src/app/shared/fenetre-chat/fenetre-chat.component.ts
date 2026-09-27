import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, effect, inject } from '@angular/core';

import { ConversationService } from '../../core/services/conversation.service';
import { ChatbotComponent } from '../../features/chatbot/chatbot.component';

// Fenêtre de conversation avec Titou (ss-fenetre-chat), posée une seule fois
// à la racine de l'application. Pas de voile : la page reste visible et
// utilisable derrière. Elle se ferme par son bouton ✕ ou la touche Échap,
// jamais par un clic à côté, pour ne pas perdre une conversation par erreur.
@Component({
  selector: 'ss-fenetre-chat',
  standalone: true,
  imports: [ChatbotComponent],
  template: `
    @if (conversation.ouverte()) {
      <section id="fenetre-chat" class="fc" role="dialog" aria-modal="false" aria-labelledby="titre-chat">
        <ss-chatbot />
      </section>
    }
  `,
  styleUrl: './fenetre-chat.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown.escape)': 'fermerAuClavier()' },
})
export class FenetreChatComponent {
  protected readonly conversation = inject(ConversationService);
  private readonly document = inject(DOCUMENT);
  // Élément qui avait le focus à l'ouverture (la bulle, un lien…) : il le retrouve à la fermeture
  private ouvreur: HTMLElement | null = null;

  constructor() {
    effect(() => {
      if (this.conversation.ouverte()) {
        this.ouvreur = this.document.activeElement as HTMLElement | null;
      } else if (this.ouvreur) {
        // Si la page a changé entre-temps, l'élément d'origine n'existe plus :
        // le focus revient alors à la bulle de chat de la nouvelle page
        const ouvreur = this.ouvreur.isConnected
          ? this.ouvreur
          : this.document.querySelector<HTMLElement>('[aria-controls="fenetre-chat"]');
        this.ouvreur = null;
        queueMicrotask(() => ouvreur?.focus());
      }
    });
  }

  protected fermerAuClavier(): void {
    // La modale d'urgence ouverte par-dessus gère elle-même sa fermeture
    if (!this.conversation.ouverte() || this.document.querySelector('.modal-urgence')) return;
    this.conversation.fermer();
  }
}
