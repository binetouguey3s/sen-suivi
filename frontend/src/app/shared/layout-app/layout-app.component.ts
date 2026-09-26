import { DOCUMENT } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
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
  { route: '/app/forum', libelle: 'Forum', icone: 'forum' },
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
  host: { '(document:keydown.escape)': 'menuOuvert.set(false)' },
})
export class LayoutAppComponent {
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  protected readonly auth = inject(AuthService);
  protected readonly modaleUrgenceOuverte = signal(false);
  protected readonly annee = new Date().getFullYear();

  // Menu burger mobile : la barre latérale s'ouvre en tiroir
  protected readonly menuOuvert = signal(false);

  constructor() {
    // La page derrière le tiroir ne défile pas tant qu'il est ouvert
    effect(() => {
      this.document.body.style.overflow = this.menuOuvert() ? 'hidden' : '';
    });
  }

  protected readonly estProfessionnel = computed(() => this.auth.typeCompte() === 'professionnel');

  // Liens selon le type de compte : utilisateur ou professionnel
  protected readonly liens = computed<LienNav[]>(() =>
    this.estProfessionnel()
      ? [
          { route: '/pro', libelle: 'Demandes', icone: 'courriel', exact: true },
          { route: '/pro/profil', libelle: 'Mon profil', libelleMobile: 'Profil', icone: 'profil' },
          { route: '/pro/disponibilites', libelle: 'Disponibilités', libelleMobile: 'Dispo', icone: 'calendrier' },
          { route: '/pro/parametres', libelle: 'Paramètres', icone: 'parametres' },
        ]
      : LIENS_UTILISATEUR,
  );

  // Navigation basse mobile, utilisateur : 2 liens, l'espace du chat, 2 liens.
  // Ressources et Lieux & Soins restent accessibles depuis le menu burger
  // plutôt que de surcharger la barre du bas à 6 entrées.
  // Professionnel : les 4 liens côte à côte, comme sur sa maquette.
  protected readonly liensMobile = computed(() => {
    const l = this.liens();
    if (this.estProfessionnel()) return { gauche: l, droite: [] };
    const choisis = [l[0], l[1], l[2], l[5]];
    return { gauche: choisis.slice(0, 2), droite: choisis.slice(2) };
  });

  // Spécialité et portrait affichés sous le nom d'un professionnel
  private readonly profilPro = httpResource<{ nom: string; specialite_affichee: string }>(() =>
    this.estProfessionnel() ? `${API_BASE_URL}/professionnels/${this.auth.identifiant()}` : undefined,
  );
  protected readonly specialite = computed(() => (this.profilPro.hasValue() ? this.profilPro.value().specialite_affichee : null));
  protected readonly portrait = computed(() => {
    const nom = this.auth.nom();
    return this.estProfessionnel() && nom ? (IMAGE_PAR_PROFESSIONNEL[nom] ?? null) : null;
  });

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
