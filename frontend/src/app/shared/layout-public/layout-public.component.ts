import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, effect, inject, signal } from '@angular/core';
import { IsActiveMatchOptions, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { IconComponent } from '../icon/icon.component';
import { ModalUrgenceComponent } from '../modal-urgence/modal-urgence.component';
import { SelecteurThemeComponent } from '../selecteur-theme/selecteur-theme.component';
import { ConversationService } from '../../core/services/conversation.service';

interface LienPublic {
  libelle: string;
  route: string;
  ancre?: string;
  exact?: boolean;
}

@Component({
  selector: 'ss-layout-public',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ModalUrgenceComponent, IconComponent, SelecteurThemeComponent],
  templateUrl: './layout-public.component.html',
  styleUrl: './layout-public.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown.escape)': 'menuOuvert.set(false)' },
})
export class LayoutPublicComponent {
  protected readonly conversation = inject(ConversationService);
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  protected readonly auth = inject(AuthService);
  protected readonly modaleUrgenceOuverte = signal(false);
  protected readonly annee = new Date().getFullYear();

  protected readonly liens: (LienPublic & { options: IsActiveMatchOptions })[] = (
    [
      { libelle: 'Découvrir', route: '/', exact: true },
      { libelle: 'Ressources', route: '/ressources' },
      { libelle: 'Lieux de détente', route: '/lieux' },
      { libelle: 'Professionnels', route: '/', ancre: 'experts', exact: true },
      { libelle: 'Forum', route: '/app/forum' },
    ] as LienPublic[]
  ).map((lien) => ({
    ...lien,
    // « Découvrir » et « Professionnels » mènent tous deux à l'accueil :
    // l'ancre (#experts) les distingue pour n'en marquer qu'un comme actif.
    options: {
      paths: lien.exact ? 'exact' : 'subset',
      fragment: lien.exact ? 'exact' : 'ignored',
      queryParams: 'ignored',
      matrixParams: 'ignored',
    },
  }));

  // Colonnes du pied de page : ouvertes sur desktop, en accordéon sur mobile
  protected readonly colonnesOuvertes = this.document.defaultView?.matchMedia('(min-width: 900px)').matches ?? true;

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
