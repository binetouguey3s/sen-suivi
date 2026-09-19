import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { ClaimsJeton, decoderJeton } from './jeton'; // ClaimsJeton signifie les informations contenues dans le jeton d'accès (access token) après décodage. decoderJeton est une fonction qui décode le jeton JWT et retourne un objet ClaimsJeton.

const CLE_ACCES = 'ss_acces';
const CLE_RAFRAICHISSEMENT = 'ss_rafraichissement';

function lireJetonValide(): ClaimsJeton | null {
  const brut = localStorage.getItem(CLE_ACCES);
  if (!brut) return null;
  const claims = decoderJeton(brut); 
  if (!claims || claims.exp * 1000 < Date.now()) return null; // Vérifie si le jeton est expiré (exp est en secondes, Date.now() en millisecondes)
  return claims; 
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly claims = signal<ClaimsJeton | null>(lireJetonValide());

  readonly estConnecte = computed(() => this.claims() !== null);
  readonly typeCompte = computed(() => this.claims()?.type_compte ?? null);
  readonly nom = computed(() => this.claims()?.nom ?? null);
  readonly prenom = computed(() => this.claims()?.prenom ?? null);

  async connecter(email: string, password: string): Promise<void> {
    try {
      const reponse = await firstValueFrom(
        this.http.post<{ access: string; refresh: string }>(`${API_BASE_URL}/auth/login`, {
          email,
          password,
        }),
      );
      localStorage.setItem(CLE_ACCES, reponse.access);
      localStorage.setItem(CLE_RAFRAICHISSEMENT, reponse.refresh);
      this.claims.set(decoderJeton(reponse.access));
    } catch (erreur) {
      throw new Error(extraireMessageErreur(erreur));
    }
  }

  deconnecter(): void {
    localStorage.removeItem(CLE_ACCES);
    localStorage.removeItem(CLE_RAFRAICHISSEMENT);
    this.claims.set(null);
  }

  jetonAcces(): string | null {
    return localStorage.getItem(CLE_ACCES);
  }
}

function extraireMessageErreur(erreur: unknown): string {
  if (erreur instanceof HttpErrorResponse) {
    const corps = erreur.error as { non_field_errors?: string[]; detail?: string } | null;
    // Messages métier explicites (ex. professionnel non validé) : gardés tels quels.
    if (corps?.non_field_errors?.length) return corps.non_field_errors[0];
    // Échec d'authentification générique de simplejwt : libellé de la maquette
    // (« Email ou mot de passe incorrect »), pas le message technique brut.
    if (corps?.detail) return 'Email ou mot de passe incorrect';
  }
  return "Une erreur est survenue. Réessayez dans un instant.";
}
