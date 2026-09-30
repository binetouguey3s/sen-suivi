import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import { API_BASE_URL } from '../../core/config/api.config';
import { EtatAcces } from '../../core/models/orientation';
import { AuthService } from '../../core/services/auth.service';
import { UrgenceService } from '../../core/services/urgence.service';
import { IconComponent } from '../icon/icon.component';

// Compteur discret de l'offre de lancement, sur les seules pages liées aux
// professionnels. On informe, on ne met pas la pression : un badge dans la
// couleur d'accent, en jours, jamais de rouge, jamais de prix, jamais de
// fenêtre surgissante. Rien du tout pour une personne en détresse.
@Component({
  selector: 'ss-badge-offre',
  standalone: true,
  imports: [IconComponent],
  template: `
    @if (jours(); as j) {
      <p class="badge-offre"><ss-icon nom="cadeau" taille="sm" /> Mise en relation gratuite encore {{ j }} {{ j > 1 ? 'jours' : 'jour' }}</p>
    }
  `,
  styles: [
    `
      .badge-offre {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin: 0;
        padding: 6px 12px;
        border-radius: var(--ss-rayon-pilule);
        background: var(--ss-accent);
        color: var(--ss-accent-texte-fort);
        font-size: 13px;
        font-weight: 600;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BadgeOffreComponent {
  private readonly auth = inject(AuthService);
  private readonly urgence = inject(UrgenceService);

  private readonly etat = httpResource<EtatAcces>(() =>
    this.auth.typeCompte() === 'utilisateur' && !this.urgence.enDetresse() ? `${API_BASE_URL}/acces/etat` : undefined,
  );

  protected readonly jours = computed(() => {
    if (this.urgence.enDetresse()) return null;
    const e = this.etat.hasValue() ? this.etat.value() : null;
    return e && !e.urgence && e.offre_active ? e.jours_restants : null;
  });
}
