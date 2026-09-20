import { HttpClient } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { AuthService } from './auth.service';

export interface Notification {
  id: number;
  canal: 'email' | 'push';
  titre: string;
  contenu: string;
  date_envoi: string;
  lue: boolean;
}

@Injectable({ providedIn: 'root' })
export class NotificationsService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly liste = signal<Notification[]>([]);
  readonly nonLues = computed(() => this.liste().filter((n) => !n.lue).length);

  constructor() {
    effect(() => {
      if (this.auth.estConnecte()) void this.charger();
      else this.liste.set([]);
    });
  }

  async charger(): Promise<void> {
    try {
      this.liste.set(await firstValueFrom(this.http.get<Notification[]>(`${API_BASE_URL}/notifications`)));
    } catch {
      this.liste.set([]);
    }
  }

  async toutLire(): Promise<void> {
    await firstValueFrom(this.http.post(`${API_BASE_URL}/notifications/tout-lire`, {}));
    this.liste.update((l) => l.map((n) => ({ ...n, lue: true })));
  }
}
