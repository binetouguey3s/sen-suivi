import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { NiveauHumeur, SuiviHumeur } from '../models/suivi';

@Injectable({ providedIn: 'root' })
export class SuiviHumeurService {
  private readonly http = inject(HttpClient);

  async publier(
    scoreHumeur: NiveauHumeur,
    options?: { note?: string; etiquettes?: string[] },
  ): Promise<SuiviHumeur> {
    return firstValueFrom(
      this.http.post<SuiviHumeur>(`${API_BASE_URL}/suivi-humeur`, {
        score_humeur: scoreHumeur,
        note: options?.note ?? '',
        etiquettes: (options?.etiquettes ?? []).join(','),
      }),
    );
  }
}
