import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';

export type StatutDemande = 'EN_ATTENTE' | 'ACCEPTEE' | 'REFUSEE';

// Demande vue par l'utilisateur (GET /api/demandes-contact)
export interface DemandeUtilisateur {
  id: number;
  professionnel: number;
  professionnel_nom: string;
  professionnel_specialite: string;
  professionnel_ville: string;
  consultation_cabinet: boolean;
  adresse_cabinet: string;
  consultation_distance: boolean;
  message: string;
  statut: StatutDemande;
  date: string;
  date_reponse: string | null;
  non_lus: number;
  dernier_message: string | null;
}

export interface MessageRelation {
  id: number;
  contenu: string;
  date: string;
  de_moi: boolean;
  lu: boolean;
}

// Mise en relation : suivi des demandes et messagerie privée après acceptation
@Injectable({ providedIn: 'root' })
export class DemandesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/demandes-contact`;

  messages(demandeId: number): Promise<MessageRelation[]> {
    return firstValueFrom(this.http.get<MessageRelation[]>(`${this.url}/${demandeId}/messages`));
  }

  envoyer(demandeId: number, contenu: string): Promise<MessageRelation> {
    return firstValueFrom(this.http.post<MessageRelation>(`${this.url}/${demandeId}/messages`, { contenu }));
  }
}
