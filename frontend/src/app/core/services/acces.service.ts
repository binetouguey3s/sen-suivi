import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { EtatAcces, MoyenPaiement } from '../models/orientation';

// Accès à la mise en relation : offre de lancement, puis accès payant.
// Le jeton d'urgence est ajouté à chaque requête par l'intercepteur.
@Injectable({ providedIn: 'root' })
export class AccesService {
  private readonly http = inject(HttpClient);

  etat(): Promise<EtatAcces> {
    return firstValueFrom(this.http.get<EtatAcces>(`${API_BASE_URL}/acces/etat`));
  }

  // Point d'entrée du paiement mobile money : renvoie le message à afficher
  async payer(moyen: MoyenPaiement, telephone: string): Promise<{ ok: boolean; message: string }> {
    try {
      await firstValueFrom(this.http.post(`${API_BASE_URL}/acces/paiement`, { moyen, telephone }));
      return { ok: true, message: 'Validez le paiement sur votre téléphone.' };
    } catch (e) {
      const corps = e instanceof HttpErrorResponse ? e.error : null;
      const message = corps?.detail ?? corps?.telephone?.[0] ?? 'Le paiement a échoué. Réessayez dans un instant.';
      return { ok: false, message };
    }
  }
}
