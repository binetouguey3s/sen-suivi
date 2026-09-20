import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ThematiqueForum } from '../models/forum';

@Injectable({ providedIn: 'root' })
export class ForumService {
  private readonly http = inject(HttpClient);

  async publier(titre: string, contenu: string, thematique: ThematiqueForum): Promise<void> {
    await firstValueFrom(
      this.http.post<{ detail: string }>(`${API_BASE_URL}/forum/publications`, { titre, contenu, thematique }),
    );
  }

  async commenter(publicationId: number, contenu: string): Promise<void> {
    await firstValueFrom(
      this.http.post<{ detail: string }>(`${API_BASE_URL}/forum/publications/${publicationId}/commentaires`, {
        contenu,
      }),
    );
  }
}
