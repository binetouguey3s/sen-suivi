import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ConversationDetail, ConversationResume, MessageAnterieur, ReponseChatbot } from '../models/chatbot';

@Injectable({ providedIn: 'root' })
export class ChatbotService {
  private readonly http = inject(HttpClient);

  async envoyer(
    message: string,
    conversationId: number | null,
    consentementConservation: boolean,
  ): Promise<ReponseChatbot> {
    return firstValueFrom(
      this.http.post<ReponseChatbot>(`${API_BASE_URL}/chatbot/message`, {
        message,
        conversation_id: conversationId ?? undefined,
        consentement_conservation: consentementConservation,
      }),
    );
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
