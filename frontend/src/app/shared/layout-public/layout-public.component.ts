import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ModalUrgenceComponent } from '../modal-urgence/modal-urgence.component';

@Component({
  selector: 'ss-layout-public',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ModalUrgenceComponent],
  templateUrl: './layout-public.component.html',
  styleUrl: './layout-public.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LayoutPublicComponent {
  protected readonly auth = inject(AuthService);
  protected readonly modaleUrgenceOuverte = signal(false);

  protected readonly initiales = computed(() => {
    const prenom = this.auth.prenom();
    const nom = this.auth.nom();
    return `${prenom?.[0] ?? ''}${nom?.[0] ?? ''}`.toUpperCase() || '?';
  });
}
