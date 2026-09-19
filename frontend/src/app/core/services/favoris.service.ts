import { HttpClient } from '@angular/common/http';
import { Injectable, effect, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class FavorisService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly ids = signal<Set<number>>(new Set());

  constructor() {
    // Charge les favoris dès qu'un utilisateur est connecté ; vide sinon.
    effect(() => {
      if (this.auth.typeCompte() === 'utilisateur') {
        void this.charger();
      } else {
        this.ids.set(new Set());
      }
    });
  }

  estFavori(id: number): boolean {
    return this.ids().has(id);
  }

  async basculer(id: number): Promise<void> {
    if (this.auth.typeCompte() !== 'utilisateur') {
      await this.router.navigateByUrl('/connexion');
      return;
    }
    const actuel = new Set(this.ids());
    if (actuel.has(id)) {
      actuel.delete(id);
      this.ids.set(actuel);
      await firstValueFrom(this.http.delete(`${API_BASE_URL}/favoris/${id}`));
    } else {
      actuel.add(id);
      this.ids.set(actuel);
      await firstValueFrom(this.http.post(`${API_BASE_URL}/favoris`, { ressource: id }));
    }
  }

  private async charger(): Promise<void> {
    try {
      const liste = await firstValueFrom(
        this.http.get<{ ressource: number }[]>(`${API_BASE_URL}/favoris`),
      );
      this.ids.set(new Set(liste.map((f) => f.ressource)));
    } catch {
      this.ids.set(new Set());
    }
  }
}
