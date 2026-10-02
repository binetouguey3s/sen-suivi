import { HttpClient, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../../../core/config/api.config';
import { VueEnsembleAdmin } from '../../../core/models/administration';
import { IconComponent } from '../../../shared/icon/icon.component';

@Component({
  selector: 'ss-admin-vue-ensemble',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './vue-ensemble.component.html',
  styleUrl: './vue-ensemble.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminVueEnsembleComponent {
  private readonly http = inject(HttpClient);

  protected readonly vue = httpResource<VueEnsembleAdmin>(() => `${API_BASE_URL}/administration/vue-ensemble`);
  protected readonly enCours = signal<number | null>(null);
  protected readonly erreur = signal<string | null>(null);

  protected moment(iso: string): string {
    return new Date(iso).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }

  // L'équipe a pris en charge la situation, selon son protocole
  protected async marquerSuivi(id: number): Promise<void> {
    this.enCours.set(id);
    this.erreur.set(null);
    try {
      await firstValueFrom(this.http.post(`${API_BASE_URL}/administration/signalements/${id}/suivi`, {}));
      this.vue.reload();
    } catch {
      this.erreur.set("L'action a échoué. Réessayez dans un instant.");
    } finally {
      this.enCours.set(null);
    }
  }
}
