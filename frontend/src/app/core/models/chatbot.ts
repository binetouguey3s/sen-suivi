// Types correspondant au sérialiseur Django (apps/chatbot), lui-même
// construit à partir de la réponse du microservice IA.

export interface RessourceSuggereeChatbot {
  ressource_id: number;
  titre: string;
  thematique: string;
}

export interface ReponseChatbot {
  conversation_id: number | null;
  reponse: string;
  source_reponse: 'REGLE' | 'RAG' | null;
  urgence: boolean;
  intention: string | null;
  ressource: RessourceSuggereeChatbot | null;
}

export interface MessageAffiche {
  id: number;
  auteur: 'UTILISATEUR' | 'BOT';
  contenu: string;
  heure: string;
  ressource?: RessourceSuggereeChatbot | null;
  urgence?: boolean;
}
