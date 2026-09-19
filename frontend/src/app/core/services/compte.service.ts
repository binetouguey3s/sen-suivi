import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { AuthService, ErreurFormulaire } from './auth.service';

export interface Compte {
  id: number;
  type_compte: 'utilisateur' | 'professionnel' | 'administrateur';
  nom: string;
  prenom: string | null;
  email: string;
  ville: string | null;
  pseudonyme: string | null;
  preferences: Record<string, { email?: boolean; push?: boolean }>;
}

@Injectable({ providedIn: 'root' })
export class CompteService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly compte = signal<Compte | null>(null);

  async charger(): Promise<Compte> {
    const compte = await firstValueFrom(this.http.get<Compte>(`${API_BASE_URL}/comptes/moi`));
    this.compte.set(compte);
    return compte;
  }

  async modifier(donnees: Partial<Pick<Compte, 'nom' | 'prenom' | 'email' | 'ville' | 'preferences'>>): Promise<Compte> {
    try {
      const compte = await firstValueFrom(this.http.patch<Compte>(`${API_BASE_URL}/comptes/moi`, donnees));
      this.compte.set(compte);
      return compte;
    } catch (e) {
      throw new ErreurFormulaire(e);
    }
  }

  async changerMotDePasse(ancien: string, nouveau: string): Promise<void> {
    try {
      await firstValueFrom(this.http.post(`${API_BASE_URL}/comptes/moi/mot-de-passe`, { ancien, nouveau }));
    } catch (e) {
      throw new ErreurFormulaire(e);
    }
  }

  async supprimer(password: string): Promise<void> {
    try {
      await firstValueFrom(this.http.request('DELETE', `${API_BASE_URL}/comptes/moi`, { body: { password } }));
    } catch (e) {
      throw new ErreurFormulaire(e);
    }
    this.auth.deconnecter();
    await this.router.navigateByUrl('/');
  }
}
