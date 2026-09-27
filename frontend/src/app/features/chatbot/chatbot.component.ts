import { ChangeDetectionStrategy, Component, ElementRef, afterNextRender, computed, effect, inject, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ConversationService } from '../../core/services/conversation.service';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../shared/modal-urgence/modal-urgence.component';

const REPONSES_RAPIDES = ['Je me sens stressé', 'Je dors mal', 'Je cherche un professionnel'];

// Contenu de la fenêtre de conversation avec Titou (ss-chatbot). La
// conversation elle-même vit dans ConversationService : fermer la fenêtre
// ou changer de page ne la perd pas.
@Component({
  selector: 'ss-chatbot',
  standalone: true,
  imports: [RouterLink, IconComponent, ModalUrgenceComponent],
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatbotComponent {
  private readonly auth = inject(AuthService);
  protected readonly conversation = inject(ConversationService);

  private readonly zoneMessages = viewChild<ElementRef<HTMLDivElement>>('zoneMessages');
  private readonly champ = viewChild<ElementRef<HTMLInputElement>>('champ');

  protected readonly reponsesRapides = REPONSES_RAPIDES;
  protected readonly saisie = signal('');
  protected readonly modaleUrgenceOuverte = signal(false);
  protected readonly estUtilisateur = computed(() => this.auth.typeCompte() === 'utilisateur');

  constructor() {
    // Fait défiler vers le bas à chaque nouveau message, et à l'ouverture
    effect(() => {
      this.conversation.messages();
      this.conversation.enCours();
      queueMicrotask(() => {
        const zone = this.zoneMessages()?.nativeElement;
        if (zone) zone.scrollTop = zone.scrollHeight;
      });
    });
    // À l'ouverture, le curseur est directement dans le champ de saisie
    afterNextRender(() => this.champ()?.nativeElement.focus());
  }

  protected saisir(evenement: Event): void {
    this.saisie.set((evenement.target as HTMLInputElement).value);
  }

  protected envoyer(texte: string): void {
    if (!texte.trim()) return;
    this.saisie.set('');
    void this.conversation.envoyer(texte);
  }
}
