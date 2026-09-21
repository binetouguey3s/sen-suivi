import { ChangeDetectionStrategy, Component, computed, inject, signal, viewChild, ElementRef, effect } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ChatbotService } from '../../core/services/chatbot.service';
import { MessageAffiche } from '../../core/models/chatbot';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../shared/modal-urgence/modal-urgence.component';

const MESSAGE_ACCUEIL =
  "Naka nga def ? Je suis là pour vous écouter. De quoi avez-vous envie de parler aujourd'hui ?";

const REPONSES_RAPIDES = ['Je me sens stressé', 'Je dors mal', 'Je cherche un professionnel'];

let compteur = 0;

@Component({
  selector: 'ss-chatbot',
  standalone: true,
  imports: [RouterLink, IconComponent, ModalUrgenceComponent],
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatbotComponent {
  protected readonly auth = inject(AuthService);
  private readonly chatbotService = inject(ChatbotService);

  private readonly zoneMessages = viewChild<ElementRef<HTMLDivElement>>('zoneMessages');

  protected readonly messages = signal<MessageAffiche[]>([
    { id: ++compteur, auteur: 'BOT', contenu: MESSAGE_ACCUEIL, heure: this.heureActuelle() },
  ]);
  protected readonly reponsesRapides = REPONSES_RAPIDES;
  protected readonly afficherReponsesRapides = computed(() => this.messages().length === 1);

  protected readonly saisie = signal('');
  protected readonly enCours = signal(false);
  protected readonly conversationId = signal<number | null>(null);
  protected readonly consentementConservation = signal(false);
  protected readonly modaleUrgenceOuverte = signal(false);

  protected readonly estUtilisateur = computed(() => this.auth.typeCompte() === 'utilisateur');

  constructor() {
    // Fait défiler vers le bas à chaque nouveau message
    effect(() => {
      this.messages();
      queueMicrotask(() => {
        const zone = this.zoneMessages()?.nativeElement;
        if (zone) zone.scrollTop = zone.scrollHeight;
      });
    });
  }

  private heureActuelle(): string {
    return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  protected saisir(evenement: Event): void {
    this.saisie.set((evenement.target as HTMLInputElement).value);
  }

  protected envoyerRapide(texte: string): void {
    void this.envoyer(texte);
  }

  protected envoyerDepuisChamp(): void {
    void this.envoyer(this.saisie());
  }

  protected async envoyer(texte: string): Promise<void> {
    const contenu = texte.trim();
    if (!contenu || this.enCours()) return;

    this.messages.update((liste) => [
      ...liste,
      { id: ++compteur, auteur: 'UTILISATEUR', contenu, heure: this.heureActuelle() },
    ]);
    this.saisie.set('');
    this.enCours.set(true);

    try {
      const reponse = await this.chatbotService.envoyer(
        contenu,
        this.conversationId(),
        this.estUtilisateur() && this.consentementConservation(),
      );
      if (reponse.conversation_id) this.conversationId.set(reponse.conversation_id);
      this.messages.update((liste) => [
        ...liste,
        {
          id: ++compteur,
          auteur: 'BOT',
          contenu: reponse.reponse,
          heure: this.heureActuelle(),
          ressource: reponse.ressource,
          urgence: reponse.urgence,
        },
      ]);
    } catch {
      this.messages.update((liste) => [
        ...liste,
        {
          id: ++compteur,
          auteur: 'BOT',
          contenu:
            "Le chatbot n'est pas disponible pour le moment. En cas de détresse immédiate, appelez le 800 805 805 ou le 1515.",
          heure: this.heureActuelle(),
        },
      ]);
    } finally {
      this.enCours.set(false);
    }
  }
}
