import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { RessourceAdmin, StatutModerationForum, StatutValidationPro } from '../models/administration';

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

  async creerRessource(donnees: Partial<RessourceAdmin>): Promise<void> {
    await firstValueFrom(this.http.post(`${API_BASE_URL}/ressources`, donnees));
  }

  async modifierRessource(id: number, donnees: Partial<RessourceAdmin>): Promise<void> {
    await firstValueFrom(this.http.patch(`${API_BASE_URL}/ressources/${id}`, donnees));
  }

  async supprimerRessource(id: number): Promise<void> {
    await firstValueFrom(this.http.delete(`${API_BASE_URL}/ressources/${id}`));
  }
}
