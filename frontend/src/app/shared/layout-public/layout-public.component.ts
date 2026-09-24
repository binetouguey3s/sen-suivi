import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { IconComponent } from '../icon/icon.component';
import { ModalUrgenceComponent } from '../modal-urgence/modal-urgence.component';

@Component({
  selector: 'ss-layout-public',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ModalUrgenceComponent, IconComponent],
  templateUrl: './layout-public.component.html',
  styleUrl: './layout-public.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown.escape)': 'menuOuvert.set(false)' },
})
export class LayoutPublicComponent {
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  protected readonly auth = inject(AuthService);
  protected readonly modaleUrgenceOuverte = signal(false);

  // Menu burger mobile (maquette accueil-mobile)
  protected readonly menuOuvert = signal(false);

  constructor() {
    // La page derrière le tiroir ne défile pas tant qu'il est ouvert
    effect(() => {
      this.document.body.style.overflow = this.menuOuvert() ? 'hidden' : '';
    });
  }

  protected readonly initiales = computed(() => {
    const prenom = this.auth.prenom();
    const nom = this.auth.nom();
    return `${prenom?.[0] ?? ''}${nom?.[0] ?? ''}`.toUpperCase() || '?';
  });

  protected readonly nomAffiche = computed(() => [this.auth.prenom(), this.auth.nom()].filter(Boolean).join(' '));

  protected deconnecter(): void {
    this.menuOuvert.set(false);
    this.auth.deconnecter();
    void this.router.navigateByUrl('/connexion');
  }
}
