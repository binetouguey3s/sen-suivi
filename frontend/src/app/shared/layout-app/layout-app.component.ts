import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { NomIcone } from '../../core/icons/icons';
import { ClocheNotificationsComponent } from '../panneau-notifications/panneau-notifications.component';
import { IconComponent } from '../icon/icon.component';
import { ModalUrgenceComponent } from '../modal-urgence/modal-urgence.component';

interface LienNav {
  route: string;
  libelle: string;
  libelleMobile?: string;
  icone: NomIcone;
  exact?: boolean;
}

const LIENS_UTILISATEUR: LienNav[] = [
  { route: '/app', libelle: 'Accueil', icone: 'accueil', exact: true },
  { route: '/app/journal', libelle: 'Mon Journal', libelleMobile: 'Journal', icone: 'journal' },
  { route: '/ressources', libelle: 'Ressources', icone: 'ressources' },
  { route: '/lieux', libelle: 'Lieux & Soins', icone: 'lieux' },
  { route: '/app/parametres', libelle: 'Paramètres', libelleMobile: 'Réglages', icone: 'parametres' },
];

@Component({
  selector: 'ss-layout-app',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent, ModalUrgenceComponent, ClocheNotificationsComponent],
  templateUrl: './layout-app.component.html',
  styleUrl: './layout-app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LayoutAppComponent {
  protected readonly auth = inject(AuthService);
  protected readonly modaleUrgenceOuverte = signal(false);

  protected readonly estProfessionnel = computed(() => this.auth.typeCompte() === 'professionnel');

  // Liens selon le type de compte : utilisateur ou professionnel
  protected readonly liens = computed<LienNav[]>(() =>
    this.estProfessionnel()
      ? [
          { route: '/pro', libelle: 'Demandes', icone: 'demandes', exact: true },
          { route: `/professionnels/${this.auth.identifiant()}`, libelle: 'Mon profil', libelleMobile: 'Profil', icone: 'profil' },
          { route: '/ressources', libelle: 'Ressources', icone: 'ressources' },
          { route: '/pro/parametres', libelle: 'Paramètres', libelleMobile: 'Réglages', icone: 'parametres' },
        ]
      : LIENS_UTILISATEUR,
  );

  // Navigation basse mobile : 2 liens, l'espace du chat, 2 liens
  protected readonly liensMobile = computed(() => {
    const l = this.liens();
    const choisis = this.estProfessionnel() ? l : [l[0], l[1], l[2], l[4]];
    return { gauche: choisis.slice(0, 2), droite: choisis.slice(2) };
  });

  protected readonly initiales = computed(() => {
    const prenom = this.auth.prenom();
    const nom = this.auth.nom();
    return `${prenom?.[0] ?? ''}${nom?.[0] ?? ''}`.toUpperCase() || '?';
  });

  protected readonly nomAffiche = computed(() => [this.auth.prenom(), this.auth.nom()].filter(Boolean).join(' '));
}
