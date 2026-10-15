import { HttpClient, HttpEventType } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { filter, firstValueFrom, lastValueFrom, tap } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ActionModeration, RessourceAdmin, StatutModerationForum, StatutValidationPro } from '../models/administration';

@Injectable({ providedIn: 'root' })
export class AdministrationService {
  private readonly http = inject(HttpClient);

  async validerProfessionnel(id: number, statut: StatutValidationPro): Promise<void> {
    await firstValueFrom(this.http.patch(`${API_BASE_URL}/professionnels/${id}`, { statut_validation: statut }));
  }

  async modererPublication(id: number, statut: StatutModerationForum): Promise<void> {
    await firstValueFrom(
      this.http.patch(`${API_BASE_URL}/forum/moderation/publications/${id}`, { statut_moderation: statut }),
    );
  }

  async modererCommentaire(id: number, statut: StatutModerationForum): Promise<void> {
    await firstValueFrom(
      this.http.patch(`${API_BASE_URL}/forum/moderation/commentaires/${id}`, { statut_moderation: statut }),
    );
  }

  // Décision humaine sur un élément de la file : elle l'emporte toujours sur celle de l'IA
  async trancher(id: number, action: ActionModeration): Promise<void> {
    await firstValueFrom(this.http.post(`${API_BASE_URL}/forum/moderation/file/${id}`, { action }));
  }

  async creerRessource(donnees: Partial<RessourceAdmin>): Promise<RessourceAdmin> {
    return firstValueFrom(this.http.post<RessourceAdmin>(`${API_BASE_URL}/ressources`, donnees));
  }

  // Fichier audio d'un podcast (multipart), avec la progression de l'envoi en pourcentage
  async envoyerAudio(id: number, fichier: File, progression: (pourcentage: number) => void): Promise<void> {
    const corps = new FormData();
    corps.append('fichier_audio', fichier);
    await lastValueFrom(
      this.http.patch(`${API_BASE_URL}/ressources/${id}`, corps, { reportProgress: true, observe: 'events' }).pipe(
        tap((evenement) => {
          if (evenement.type === HttpEventType.UploadProgress && evenement.total) {
            progression(Math.round((evenement.loaded / evenement.total) * 100));
          }
        }),
        filter((evenement) => evenement.type === HttpEventType.Response),
      ),
    );
  }

  async retirerAudio(id: number): Promise<void> {
    await firstValueFrom(this.http.patch(`${API_BASE_URL}/ressources/${id}`, { fichier_audio: null }));
  }

  async modifierRessource(id: number, donnees: Partial<RessourceAdmin>): Promise<void> {
    await firstValueFrom(this.http.patch(`${API_BASE_URL}/ressources/${id}`, donnees));
  }

  async supprimerRessource(id: number): Promise<void> {
    await firstValueFrom(this.http.delete(`${API_BASE_URL}/ressources/${id}`));
  }
}
