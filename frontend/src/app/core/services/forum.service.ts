import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ThematiqueForum } from '../models/forum';

export type TypeMessageForum = 'PUBLICATION' | 'COMMENTAIRE';

// Message envoyé : enregistré, puis modéré en arrière-plan
export interface MessageEnvoye {
  id: number;
  statut_moderation: string;
  detail: string;
}

// GET /api/forum/mes-messages : suivi par l'auteur de ses propres messages
export interface MonMessageForum {
  type: TypeMessageForum;
  id: number;
  titre: string;
  contenu: string;
  date: string;
  statut_moderation: 'EN_ATTENTE' | 'VISIBLE' | 'MASQUE' | 'SUPPRIME' | 'BLOQUE';
  message: string;
  peut_contester: boolean;
  conteste: boolean;
}

export interface MesMessagesForum {
  suspendu_jusqu_au: string | null;
  messages: MonMessageForum[];
}

@Injectable({ providedIn: 'root' })
export class ForumService {
  private readonly http = inject(HttpClient);

  publier(titre: string, contenu: string, thematique: ThematiqueForum): Promise<MessageEnvoye> {
    return firstValueFrom(this.http.post<MessageEnvoye>(`${API_BASE_URL}/forum/publications`, { titre, contenu, thematique }));
  }

  commenter(publicationId: number, contenu: string): Promise<MessageEnvoye> {
    return firstValueFrom(
      this.http.post<MessageEnvoye>(`${API_BASE_URL}/forum/publications/${publicationId}/commentaires`, { contenu }),
    );
  }

  mesMessages(): Promise<MesMessagesForum> {
    return firstValueFrom(this.http.get<MesMessagesForum>(`${API_BASE_URL}/forum/mes-messages`));
  }

  // Droit de contestation : réexamen humain d'une décision automatique
  contester(type: TypeMessageForum, id: number, motif: string): Promise<{ detail: string }> {
    const chemin = type === 'PUBLICATION' ? 'publication' : 'commentaire';
    return firstValueFrom(
      this.http.post<{ detail: string }>(`${API_BASE_URL}/forum/mes-messages/${chemin}/${id}/contester`, { motif }),
    );
  }
}
