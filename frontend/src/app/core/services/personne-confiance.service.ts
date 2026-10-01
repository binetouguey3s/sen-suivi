import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ErreurFormulaire } from './auth.service';

export interface PersonneConfiance {
  prenom: string;
  lien: string;
  telephone: string;
  email: string;
  accord_confirme: boolean;
  // Consentement séparé : e-mail automatique en cas de risque vital (jamais pour des violences)
  alerte_automatique: boolean;
  // Message proposé pour le SMS : aucun détail des échanges
  message_sms?: string;
  alerte_email_disponible?: boolean;
}

export type CanalAlerte = 'APPEL' | 'SMS' | 'EMAIL';

// Proche que l'utilisateur peut faire prévenir s'il va très mal : jamais
// automatiquement, toujours à sa demande.
@Injectable({ providedIn: 'root' })
export class PersonneConfianceService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/comptes/moi/personne-confiance`;

  charger(): Promise<PersonneConfiance | null> {
    return firstValueFrom(this.http.get<PersonneConfiance | null>(this.url));
  }

  async enregistrer(personne: PersonneConfiance): Promise<PersonneConfiance> {
    try {
      return await firstValueFrom(this.http.put<PersonneConfiance>(this.url, personne));
    } catch (e) {
      throw new ErreurFormulaire(e);
    }
  }

  async supprimer(): Promise<void> {
    await firstValueFrom(this.http.delete(this.url));
  }

  alerter(canal: CanalAlerte): Promise<{ detail: string }> {
    return firstValueFrom(this.http.post<{ detail: string }>(`${this.url}/alerte`, { canal }));
  }
}
