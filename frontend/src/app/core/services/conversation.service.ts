import { Injectable, computed, effect, inject, signal, untracked } from '@angular/core';

import { MessageAffiche } from '../models/chatbot';
import { AuthService } from './auth.service';
import { ChatbotService } from './chatbot.service';

const MESSAGE_ACCUEIL =
  "Naka nga def ? Je suis là pour vous écouter. De quoi avez-vous envie de parler aujourd'hui ?";

const MESSAGE_INDISPONIBLE =
  "Le chatbot n'est pas disponible pour le moment. En cas de détresse immédiate, appelez le 800 805 805 ou le 1515.";

// Conversation avec Titou et état de sa fenêtre. Porté par un service pour
// survivre à la fermeture de la fenêtre et aux changements de page ; effacé
// dès que le compte connecté change, pour ne rien laisser sur un appareil partagé.
@Injectable({ providedIn: 'root' })
export class ConversationService {
  private readonly auth = inject(AuthService);
  private readonly chatbot = inject(ChatbotService);
  private compteur = 0;

  private readonly ouverteInterne = signal(false);
  private readonly messagesInternes = signal<MessageAffiche[]>([]);
  private readonly enCoursInterne = signal(false);
  private readonly conversationId = signal<number | null>(null);

  readonly ouverte = this.ouverteInterne.asReadonly();
  readonly messages = this.messagesInternes.asReadonly();
  readonly enCours = this.enCoursInterne.asReadonly();
  // Les réponses rapides ne sont proposées qu'avant le premier message
  readonly debutDeConversation = computed(() => this.messagesInternes().length === 1);
  readonly consentementConservation = signal(false);

  constructor() {
    this.reinitialiser();
    // Déconnexion ou changement de compte : nouvelle conversation, fenêtre fermée
    effect(() => {
      this.auth.identifiant();
      untracked(() => {
        this.reinitialiser();
        this.ouverteInterne.set(false);
      });
    });
  }

  ouvrir(): void {
    this.ouverteInterne.set(true);
  }

  fermer(): void {
    this.ouverteInterne.set(false);
  }

  basculer(): void {
    this.ouverteInterne.update((ouverte) => !ouverte);
  }

  async envoyer(texte: string): Promise<void> {
    const contenu = texte.trim();
    if (!contenu || this.enCoursInterne()) return;

    this.ajouter({ auteur: 'UTILISATEUR', contenu });
    this.enCoursInterne.set(true);
    const conserver = this.auth.typeCompte() === 'utilisateur' && this.consentementConservation();

    try {
      const reponse = await this.chatbot.envoyer(contenu, this.conversationId(), conserver);
      if (reponse.conversation_id) this.conversationId.set(reponse.conversation_id);
      this.ajouter({ auteur: 'BOT', contenu: reponse.reponse, ressource: reponse.ressource, urgence: reponse.urgence });
    } catch {
      this.ajouter({ auteur: 'BOT', contenu: MESSAGE_INDISPONIBLE });
    } finally {
      this.enCoursInterne.set(false);
    }
  }

  private reinitialiser(): void {
    this.messagesInternes.set([]);
    this.conversationId.set(null);
    this.consentementConservation.set(false);
    this.ajouter({ auteur: 'BOT', contenu: MESSAGE_ACCUEIL });
  }

  private ajouter(message: Omit<MessageAffiche, 'id' | 'heure'>): void {
    const heure = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    this.messagesInternes.update((liste) => [...liste, { ...message, id: ++this.compteur, heure }]);
  }
}
