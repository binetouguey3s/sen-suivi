import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { NomIcone } from '../../core/icons/icons';
import { AuthService } from '../../core/services/auth.service';
import { IconComponent } from '../icon/icon.component';

interface LienNavAdmin {
  route: string;
  libelle: string;
  icone: NomIcone;
  exact?: boolean;
}

const LIENS: LienNavAdmin[] = [
  { route: '/admin', libelle: "Vue d'ensemble", icone: 'journal', exact: true },
  { route: '/admin/professionnels', libelle: 'Professionnels', icone: 'utilisateur' },
  { route: '/admin/forum', libelle: 'Forum', icone: 'forum' },
  { route: '/admin/ressources', libelle: 'Ressources', icone: 'ressources' },
];

// Écrans d'administration (docs/CONTEXTE.md section 6) : fond blanc pur, aucun
// dégradé côté contenu ; la barre latérale sombre reprend la structure de
// la maquette « Sen Suivi - Administration » pour distinguer cet espace.
@Component({
  selector: 'ss-layout-admin',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent],
  templateUrl: './layout-admin.component.html',
  styleUrl: './layout-admin.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown.escape)': 'menuOuvert.set(false)' },
})
export class LayoutAdminComponent {
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  protected readonly auth = inject(AuthService);

  protected readonly liens = LIENS;
  protected readonly menuOuvert = signal(false);

  constructor() {
    // La page derrière le tiroir ne défile pas tant qu'il est ouvert
    effect(() => {
      this.document.body.style.overflow = this.menuOuvert() ? 'hidden' : '';
    });
  }

  protected readonly initiales = computed(() => (this.auth.nom() ?? '?').slice(0, 2).toUpperCase());

  protected deconnecter(): void {
    this.menuOuvert.set(false);
    this.auth.deconnecter();
    void this.router.navigateByUrl('/connexion');
  }
}
