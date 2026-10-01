import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ConversationDetail, ConversationResume, EchangePrecedent, MessageAnterieur, ReponseChatbot } from '../models/chatbot';

@Injectable({ providedIn: 'root' })
export class ChatbotService {
  private readonly http = inject(HttpClient);

  async envoyer(
    message: string,
    conversationId: number | null,
    consentementConservation: boolean,
    historique: EchangePrecedent[] = [],
  ): Promise<ReponseChatbot> {
    return firstValueFrom(
      this.http.post<ReponseChatbot>(`${API_BASE_URL}/chatbot/message`, {
        message,
        conversation_id: conversationId ?? undefined,
        consentement_conservation: consentementConservation,
        historique,
      }),
    );
  }

  // --- Vocal ---

  // L'audio part en mémoire vers le serveur, qui le transcrit puis le traite
  // exactement comme un message tapé
  async envoyerVocal(
    audio: Blob,
    duree: number,
    conversationId: number | null,
    consentementConservation: boolean,
    historique: EchangePrecedent[] = [],
  ): Promise<ReponseChatbot> {
    const extension = audio.type.includes('mp4') ? 'm4a' : audio.type.includes('ogg') ? 'ogg' : 'webm';
    const donnees = new FormData();
    donnees.append('audio', audio, `voix.${extension}`);
    donnees.append('duree', String(Math.round(duree)));
    donnees.append('historique', JSON.stringify(historique));
    donnees.append('consentement_conservation', String(consentementConservation));
    if (conversationId) donnees.append('conversation_id', String(conversationId));
    return firstValueFrom(this.http.post<ReponseChatbot>(`${API_BASE_URL}/chatbot/message-vocal`, donnees));
  }

  // Audio d'une réponse validée, ou null si la synthèse n'est pas disponible
  async lireAVoixHaute(texte: string, jetonVocal: string): Promise<Blob | null> {
    const reponse = await firstValueFrom(
      this.http.post(`${API_BASE_URL}/chatbot/reponse-vocale`, { texte, jeton_vocal: jetonVocal }, {
        observe: 'response',
        responseType: 'blob',
      }),
    );
    return reponse.status === 200 && reponse.body?.size ? reponse.body : null;
  }

  // --- Historique (comptes utilisateur, conversations conservées) ---

  lister(): Promise<ConversationResume[]> {
    return firstValueFrom(this.http.get<ConversationResume[]>(`${API_BASE_URL}/chatbot/conversations`));
  }

  lire(id: number): Promise<ConversationDetail> {
    return firstValueFrom(this.http.get<ConversationDetail>(`${API_BASE_URL}/chatbot/conversations/${id}`));
  }

  // Enregistre d'un coup les messages déjà échangés, au moment du consentement
  async creer(messages: MessageAnterieur[]): Promise<number> {
    const { id } = await firstValueFrom(
      this.http.post<{ id: number }>(`${API_BASE_URL}/chatbot/conversations`, { messages }),
    );
    return id;
  }

  async supprimer(id: number): Promise<void> {
    await firstValueFrom(this.http.delete(`${API_BASE_URL}/chatbot/conversations/${id}`));
  }
}
