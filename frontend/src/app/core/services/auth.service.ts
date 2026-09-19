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

  async inscrireUtilisateur(donnees: {
    prenom: string;
    nom: string;
    email: string;
    password: string;
  }): Promise<void> {
    await this.envoyer(`${API_BASE_URL}/auth/register`, donnees);
  }

  async inscrireProfessionnel(donnees: Record<string, unknown>): Promise<void> {
    await this.envoyer(`${API_BASE_URL}/professionnels/inscription`, donnees);
  }

  async demanderReinitialisation(email: string): Promise<void> {
    await this.envoyer(`${API_BASE_URL}/auth/mot-de-passe-oublie`, { email });
  }

  async confirmerReinitialisation(uid: string, token: string, password: string): Promise<void> {
    await this.envoyer(`${API_BASE_URL}/auth/mot-de-passe-oublie/confirmer`, { uid, token, password });
  }

  // POST public : en cas d'erreur 400, lève une ErreurFormulaire avec les messages par champ.
  private async envoyer(url: string, corps: unknown): Promise<void> {
    try {
      await firstValueFrom(this.http.post(url, corps));
    } catch (erreur) {
      throw new ErreurFormulaire(erreur);
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

export class ErreurFormulaire extends Error {
  /** Messages par champ (clé « general » pour les erreurs non liées à un champ). */
  readonly champs: Record<string, string> = {};

  constructor(erreur: unknown) {
    super('Erreur de formulaire');
    if (erreur instanceof HttpErrorResponse && erreur.status === 400 && erreur.error) {
      const corps = erreur.error as unknown;
      if (Array.isArray(corps)) {
        this.champs['general'] = String(corps[0]);
      } else if (typeof corps === 'object') {
        for (const [cle, valeur] of Object.entries(corps as Record<string, unknown>)) {
          const message = Array.isArray(valeur) ? String(valeur[0]) : String(valeur);
          this.champs[cle === 'non_field_errors' || cle === 'detail' ? 'general' : cle] = message;
        }
      }
    }
    if (!Object.keys(this.champs).length) {
      this.champs['general'] = 'Une erreur est survenue. Réessayez dans un instant.';
    }
  }
}
