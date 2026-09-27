import { ChangeDetectionStrategy, Component, ElementRef, afterNextRender, effect, inject, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';

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
  protected readonly conversation = inject(ConversationService);

  private readonly zoneMessages = viewChild<ElementRef<HTMLDivElement>>('zoneMessages');
  private readonly champ = viewChild<ElementRef<HTMLInputElement>>('champ');

  protected readonly reponsesRapides = REPONSES_RAPIDES;
  protected readonly saisie = signal('');
  protected readonly modaleUrgenceOuverte = signal(false);
  // Conversation dont la suppression attend confirmation dans la liste
  protected readonly aConfirmer = signal<number | null>(null);
  protected readonly suppressionEchouee = signal(false);

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

  protected changerConservation(evenement: Event): void {
    void this.conversation.definirConservation((evenement.target as HTMLInputElement).checked);
  }

  protected async supprimer(id: number): Promise<void> {
    this.suppressionEchouee.set(false);
    try {
      await this.conversation.supprimer(id);
      this.aConfirmer.set(null);
    } catch {
      this.suppressionEchouee.set(true);
    }
  }

  // « Aujourd'hui à 18:15 », « Hier à 09:02 » ou « 12 sept. à 21:40 »
  protected dateLisible(iso: string): string {
    const date = new Date(iso);
    const heure = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const jour = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    const ecart = Math.round((jour(new Date()) - jour(date)) / 86_400_000);
    if (ecart === 0) return `Aujourd'hui à ${heure}`;
    if (ecart === 1) return `Hier à ${heure}`;
    return `${date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} à ${heure}`;
  }
}
