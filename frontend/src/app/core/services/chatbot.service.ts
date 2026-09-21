import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ReponseChatbot } from '../models/chatbot';

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
}
