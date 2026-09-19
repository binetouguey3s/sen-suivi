import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { IconComponent } from '../icon/icon.component';
import { ModalUrgenceComponent } from '../modal-urgence/modal-urgence.component';
import { AuthService } from '../../core/services/auth.service';
import { NomIcone } from '../../core/icons/icons';

interface LienNav {
  route: string;
  libelle: string;
  icone: NomIcone;
  disponible: boolean;
}

// Les routes non encore construites restent visibles (fidélité à la maquette)
// mais ne naviguent pas : /** redirige vers /connexion, ce qui déconnecterait
// visuellement un utilisateur qui cliquerait dessus avant qu'elles existent.
const LIENS_NAV: LienNav[] = [
  { route: '/app', libelle: 'Accueil', icone: 'accueil', disponible: true },
  { route: '/app/journal', libelle: 'Mon Journal', icone: 'journal', disponible: true },
  { route: '/ressources', libelle: 'Ressources', icone: 'ressources', disponible: true },
  { route: '/app/lieux', libelle: 'Lieux & Soins', icone: 'lieux', disponible: false },
  { route: '/app/parametres', libelle: 'Paramètres', icone: 'parametres', disponible: false },
];

@Component({
  selector: 'ss-layout-app',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent, ModalUrgenceComponent],
  templateUrl: './layout-app.component.html',
  styleUrl: './layout-app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LayoutAppComponent {
  protected readonly auth = inject(AuthService);
  protected readonly liens = LIENS_NAV;
  protected readonly modaleUrgenceOuverte = signal(false);

  protected readonly initiales = computed(() => {
    const prenom = this.auth.prenom();
    const nom = this.auth.nom();
    return `${prenom?.[0] ?? ''}${nom?.[0] ?? ''}`.toUpperCase() || '?';
  });
}
