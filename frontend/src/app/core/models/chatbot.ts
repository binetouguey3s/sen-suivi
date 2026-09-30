// Types correspondant au sérialiseur Django (apps/chatbot), lui-même
// construit à partir de la réponse du microservice IA.

import { ProfessionnelSuggereChatbot } from './orientation';

export interface RessourceSuggereeChatbot {
  ressource_id: number;
  titre: string;
  thematique: string;
}

export interface ReponseChatbot {
  conversation_id: number | null;
  reponse: string;
  source_reponse: 'REGLE' | 'RAG' | 'GENERATION' | null;
  urgence: boolean;
  intention: string | null;
  ressource: RessourceSuggereeChatbot | null;
  orientation_professionnel?: boolean;
  // Professionnel mis en avant par l'algorithme d'orientation (compte connecté)
  professionnel_suggere?: ProfessionnelSuggereChatbot | null;
  // Remis seulement quand une détresse est détectée
  jeton_urgence?: string | null;
}

export interface MessageAffiche {
  id: number;
  auteur: 'UTILISATEUR' | 'BOT';
  contenu: string;
  heure: string;
  ressource?: RessourceSuggereeChatbot | null;
  urgence?: boolean;
  professionnel?: ProfessionnelSuggereChatbot | null;
  // Titou oriente vers un professionnel sans suggestion personnalisée (visiteur)
  orientationAnnuaire?: boolean;
}

// Historique des conversations conservées (GET /api/chatbot/conversations)
export interface ConversationResume {
  id: number;
  date: string;
  derniere_activite: string;
  nombre_messages: number;
  apercu: string;
}

export interface MessageHistorique {
  id: number;
  auteur: 'UTILISATEUR' | 'BOT';
  contenu: string;
  date_envoi: string;
  urgence: boolean;
  ressource: RessourceSuggereeChatbot | null;
}

export interface ConversationDetail {
  id: number;
  date: string;
  messages: MessageHistorique[];
}

// Message déjà échangé, envoyé au moment où l'utilisateur accepte la conservation
export interface MessageAnterieur {
  auteur: 'UTILISATEUR' | 'BOT';
  contenu: string;
  urgence?: boolean;
  ressource_id?: number | null;
}

// Échange déjà affiché, transmis pour que Titou suive la conversation
export interface EchangePrecedent {
  auteur: 'UTILISATEUR' | 'BOT';
  contenu: string;
}
