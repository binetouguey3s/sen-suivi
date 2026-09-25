import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ErreurFormulaire } from './auth.service';

// Fiche publique du professionnel connecté (GET/PATCH /api/professionnels/moi)
export interface FicheProfessionnel {
  id: number;
  nom: string;
  specialite_affichee: string;
  ville: string;
  langue: string;
  tarif_indicatif: number;
  presentation: string;
  domaines: string[];
  consultation_cabinet: boolean;
  adresse_cabinet: string;
  consultation_distance: boolean;
}

export type ModificationFiche = Partial<Omit<FicheProfessionnel, 'id' | 'nom' | 'specialite_affichee'>>;

@Injectable({ providedIn: 'root' })
export class FicheProfessionnelService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/professionnels/moi`;

  charger(): Promise<FicheProfessionnel> {
    return firstValueFrom(this.http.get<FicheProfessionnel>(this.url));
  }

  async modifier(donnees: ModificationFiche): Promise<FicheProfessionnel> {
    try {
      return await firstValueFrom(this.http.patch<FicheProfessionnel>(this.url, donnees));
    } catch (e) {
      throw new ErreurFormulaire(e);
    }
  }
}
