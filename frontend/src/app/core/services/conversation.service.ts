import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal, untracked } from '@angular/core';

import { ConversationResume, MessageAffiche, MessageHistorique, ReponseChatbot } from '../models/chatbot';
import { AuthService } from './auth.service';
import { ChatbotService } from './chatbot.service';
import { UrgenceService } from './urgence.service';

const MESSAGE_ACCUEIL =
  "Naka nga def ? Je suis là pour vous écouter. De quoi avez-vous envie de parler aujourd'hui ?";

// Derniers échanges transmis à Titou pour qu'il suive la conversation
const HISTORIQUE_TRANSMIS = 6;

const MESSAGE_INDISPONIBLE =
  "Le chatbot n'est pas disponible pour le moment. En cas de détresse immédiate, appelez le 800 805 805 ou le 1515.";
const MESSAGE_VOCAL_INDISPONIBLE =
  "Je n'ai pas pu recevoir votre message vocal. Vous pouvez réessayer ou l'écrire. En cas de détresse immédiate, appelez le 800 805 805 ou le 1515.";

export type VueChat = 'conversation' | 'historique';
export type EtatHistorique = 'chargement' | 'pret' | 'erreur';

function heureDe(date: Date): string {
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

// Conversation avec Titou et état de sa fenêtre. Porté par un service pour
// survivre à la fermeture de la fenêtre et aux changements de page ; effacé
// dès que le compte connecté change, pour ne rien laisser sur un appareil partagé.
// Un compte utilisateur peut conserver ses échanges, les relire et les effacer.
@Injectable({ providedIn: 'root' })
export class ConversationService {
  private readonly auth = inject(AuthService);
  private readonly chatbot = inject(ChatbotService);
  private readonly urgence = inject(UrgenceService);
  private compteur = 0;

  private readonly ouverteInterne = signal(false);
  private readonly messagesInternes = signal<MessageAffiche[]>([]);
  private readonly enCoursInterne = signal(false);
  private readonly conversationId = signal<number | null>(null);
  private readonly consentementInterne = signal(false);
  private readonly erreurConservationInterne = signal(false);
  private readonly vueInterne = signal<VueChat>('conversation');
  private readonly historiqueInterne = signal<ConversationResume[]>([]);
  private readonly etatHistoriqueInterne = signal<EtatHistorique>('chargement');

  readonly ouverte = this.ouverteInterne.asReadonly();
  readonly messages = this.messagesInternes.asReadonly();
  readonly enCours = this.enCoursInterne.asReadonly();
  readonly consentementConservation = this.consentementInterne.asReadonly();
  readonly erreurConservation = this.erreurConservationInterne.asReadonly();
  readonly vue = this.vueInterne.asReadonly();
  readonly historique = this.historiqueInterne.asReadonly();
  readonly etatHistorique = this.etatHistoriqueInterne.asReadonly();
  // Les réponses rapides ne sont proposées qu'avant le premier message
  readonly debutDeConversation = computed(() => this.messagesInternes().length === 1);
  // Conserver et relire son historique : réservé aux comptes utilisateur
  readonly peutConserver = computed(() => this.auth.typeCompte() === 'utilisateur');
  readonly idConversationAffichee = this.conversationId.asReadonly();

  constructor() {
    this.reinitialiser();
    // Déconnexion ou changement de compte : nouvelle conversation, fenêtre fermée
    effect(() => {
      this.auth.identifiant();
      untracked(() => {
        this.reinitialiser();
        this.historiqueInterne.set([]);
        this.vueInterne.set('conversation');
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

    const historique = this.echangesRecents();
    this.ajouter({ auteur: 'UTILISATEUR', contenu });
    this.enCoursInterne.set(true);
    const conserver = this.peutConserver() && this.consentementInterne();

    try {
      this.recevoir(await this.chatbot.envoyer(contenu, this.conversationId(), conserver, historique));
    } catch {
      this.ajouter({ auteur: 'BOT', contenu: MESSAGE_INDISPONIBLE });
    } finally {
      this.enCoursInterne.set(false);
    }
  }

  // Message vocal : la transcription s'affiche comme message de la personne,
  // modifiable, puis Titou répond exactement comme à un message tapé
  async envoyerVocal(audio: Blob, duree: number): Promise<void> {
    if (this.enCoursInterne()) return;
    const historique = this.echangesRecents();
    this.enCoursInterne.set(true);
    const conserver = this.peutConserver() && this.consentementInterne();

    try {
      const reponse = await this.chatbot.envoyerVocal(audio, duree, this.conversationId(), conserver, historique);
      if (reponse.transcription) this.ajouter({ auteur: 'UTILISATEUR', contenu: reponse.transcription, vocal: true });
      this.recevoir(reponse);
    } catch (e) {
      const detail = e instanceof HttpErrorResponse ? (e.error?.detail ?? e.error?.duree?.[0]) : null;
      this.ajouter({ auteur: 'BOT', contenu: detail ?? MESSAGE_VOCAL_INDISPONIBLE });
    } finally {
      this.enCoursInterne.set(false);
    }
  }

  // Échanges déjà affichés, sans le message d'accueil (toujours le même)
  private echangesRecents() {
    return this.messagesInternes()
      .slice(1)
      .slice(-HISTORIQUE_TRANSMIS)
      .map((m) => ({ auteur: m.auteur, contenu: m.contenu }));
  }

  private recevoir(reponse: ReponseChatbot): void {
    if (reponse.conversation_id) this.conversationId.set(reponse.conversation_id);
    // Détresse : la mise en relation devient gratuite et sans écran de paiement
    if (reponse.jeton_urgence) this.urgence.memoriser(reponse.jeton_urgence);
    this.ajouter({
      auteur: 'BOT',
      contenu: reponse.reponse,
      ressource: reponse.ressource,
      urgence: reponse.urgence,
      professionnel: reponse.professionnel_suggere ?? null,
      orientationAnnuaire: !!reponse.orientation_professionnel && !reponse.professionnel_suggere,
      jetonVocal: reponse.jeton_vocal ?? null,
      personnePrevenue: reponse.personne_confiance_prevenue ?? null,
    });
  }

  // Cocher la case enregistre aussi les messages déjà échangés : l'historique
  // est complet. En cas d'échec, la case se décoche : on ne laisse jamais
  // croire qu'un échange est conservé alors qu'il ne l'est pas.
  async definirConservation(conserver: boolean): Promise<void> {
    this.erreurConservationInterne.set(false);
    this.consentementInterne.set(conserver);
    const dejaEchanges = this.messagesInternes().slice(1);
    if (!conserver || !this.peutConserver() || this.conversationId() !== null || dejaEchanges.length === 0) return;

    try {
      const id = await this.chatbot.creer(
        dejaEchanges.map((m) => ({
          auteur: m.auteur,
          contenu: m.contenu,
          urgence: !!m.urgence,
          ressource_id: m.ressource?.ressource_id ?? null,
        })),
      );
      this.conversationId.set(id);
    } catch {
      this.consentementInterne.set(false);
      this.erreurConservationInterne.set(true);
    }
  }

  // --- Historique -------------------------------------------------------------

  async afficherHistorique(): Promise<void> {
    this.vueInterne.set('historique');
    this.etatHistoriqueInterne.set('chargement');
    try {
      this.historiqueInterne.set(await this.chatbot.lister());
      this.etatHistoriqueInterne.set('pret');
    } catch {
      this.etatHistoriqueInterne.set('erreur');
    }
  }

  afficherConversation(): void {
    this.vueInterne.set('conversation');
  }

  // Rouvre une conversation conservée : on peut la relire et la continuer
  async reprendre(id: number): Promise<void> {
    try {
      const detail = await this.chatbot.lire(id);
      this.messagesInternes.set([this.messageAccueil(), ...detail.messages.map((m) => this.depuisHistorique(m))]);
      this.conversationId.set(detail.id);
      this.consentementInterne.set(true);
      this.erreurConservationInterne.set(false);
      this.vueInterne.set('conversation');
    } catch {
      this.etatHistoriqueInterne.set('erreur');
    }
  }

  async supprimer(id: number): Promise<void> {
    await this.chatbot.supprimer(id);
    this.historiqueInterne.update((liste) => liste.filter((c) => c.id !== id));
    // La conversation affichée vient d'être effacée : on repart de zéro
    if (this.conversationId() === id) this.reinitialiser();
  }

  nouvelleConversation(): void {
    this.reinitialiser();
    this.vueInterne.set('conversation');
  }

  private reinitialiser(): void {
    this.messagesInternes.set([this.messageAccueil()]);
    this.conversationId.set(null);
    this.consentementInterne.set(false);
    this.erreurConservationInterne.set(false);
  }

  private messageAccueil(): MessageAffiche {
    return { id: ++this.compteur, auteur: 'BOT', contenu: MESSAGE_ACCUEIL, heure: heureDe(new Date()) };
  }

  private depuisHistorique(m: MessageHistorique): MessageAffiche {
    return {
      id: ++this.compteur,
      auteur: m.auteur,
      contenu: m.contenu,
      heure: heureDe(new Date(m.date_envoi)),
      ressource: m.ressource,
      urgence: m.urgence,
    };
  }

  private ajouter(message: Omit<MessageAffiche, 'id' | 'heure'>): void {
    this.messagesInternes.update((liste) => [...liste, { ...message, id: ++this.compteur, heure: heureDe(new Date()) }]);
  }
}
