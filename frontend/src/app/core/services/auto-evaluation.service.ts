import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ResultatEvaluation, TypeEvaluation } from '../models/evaluation';

@Injectable({ providedIn: 'root' })
export class AutoEvaluationService {
  private readonly http = inject(HttpClient);

  // Dernier résultat, conservé pour l'écran de résultats (pas de GET dédié
  // dans l'API : le résultat n'est renvoyé que par le POST).
  readonly dernierResultat = signal<ResultatEvaluation | null>(null);

  async soumettre(
    type: TypeEvaluation,
    reponses: { question: number; option: number }[],
  ): Promise<ResultatEvaluation> {
    const resultat = await firstValueFrom(
      this.http.post<ResultatEvaluation>(`${API_BASE_URL}/auto-evaluations`, {
        type_evaluation: type,
        reponses,
      }),
    );
    this.dernierResultat.set(resultat);
    return resultat;
  }
}
