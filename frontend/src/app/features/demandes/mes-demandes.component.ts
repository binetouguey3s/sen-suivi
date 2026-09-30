import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { DemandeUtilisateur } from '../../core/services/demandes.service';
import { IconComponent } from '../../shared/icon/icon.component';

const LIBELLE_STATUT = { EN_ATTENTE: 'En attente', ACCEPTEE: 'Acceptée', REFUSEE: 'Déclinée' } as const;

// Suivi des demandes de mise en relation de l'utilisateur, et accès à la
// conversation privée une fois la demande acceptée.
@Component({
  selector: 'ss-mes-demandes',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './mes-demandes.component.html',
  styleUrl: './mes-demandes.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MesDemandesComponent {
  protected readonly demandes = httpResource<DemandeUtilisateur[]>(() => `${API_BASE_URL}/demandes-contact`, {
    defaultValue: [],
  });
  protected readonly liste = computed(() => (this.demandes.hasValue() ? this.demandes.value() : []));
  protected readonly libelleStatut = LIBELLE_STATUT;

  protected modalites(d: DemandeUtilisateur): string {
    if (d.consultation_distance && d.consultation_cabinet) return ', à distance ou en cabinet';
    if (d.consultation_distance) return ', à distance';
    return d.consultation_cabinet ? ', en cabinet' : '';
  }

  protected date(iso: string): string {
    return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  }
}
