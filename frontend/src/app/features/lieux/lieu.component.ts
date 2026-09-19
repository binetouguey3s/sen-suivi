import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_LIEU } from '../../core/config/images-lieux';
import { LieuDetente } from '../../core/models/suivi';
import { distanceKm, lienItineraire } from '../../core/utils/lieux';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../shared/modal-urgence/modal-urgence.component';

@Component({
  selector: 'ss-lieu',
  standalone: true,
  imports: [RouterLink, IconComponent, CarteLieuxComponent, ModalUrgenceComponent],
  templateUrl: './lieu.component.html',
  styleUrl: './lieu.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LieuComponent {
  // Paramètre de route :id (withComponentInputBinding)
  readonly id = input.required<string>();

  protected readonly lieu = httpResource<LieuDetente>(() => `${API_BASE_URL}/lieux/${this.id()}`);
  private readonly tous = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, { defaultValue: [] });

  protected readonly modaleUrgenceOuverte = signal(false);

  protected readonly itineraire = computed(() => {
    const l = this.lieu.value();
    return l && l.latitude !== null ? lienItineraire(l) : null;
  });

  protected readonly proches = computed(() => {
    const courant = this.lieu.value();
    if (!courant) return [];
    return this.tous
      .value()
      .filter((l) => l.id !== courant.id)
      .sort((a, b) => distanceKm(courant, a) - distanceKm(courant, b))
      .slice(0, 3);
  });

  protected readonly pourCarte = computed(() => {
    const l = this.lieu.value();
    return l ? [l] : [];
  });

  protected image(lieu: LieuDetente): string | null {
    return IMAGE_PAR_LIEU[lieu.nom] ?? null;
  }
}
