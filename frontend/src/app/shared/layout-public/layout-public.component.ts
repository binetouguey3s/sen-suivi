import { DOCUMENT, ViewportScroller } from '@angular/common';
import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, computed, effect, inject, signal, viewChild } from '@angular/core';
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
      { libelle: 'Professionnels', route: '/professionnels' },
      { libelle: 'Forum', route: '/app/forum' },
    ] as LienPublic[]
  ).map((lien) => ({
    ...lien,
    // « Découvrir » n'est actif que sur l'accueil lui-même, sans ancre ;
    // les autres le restent sur leurs sous-pages (une fiche, un lieu…).
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

  private readonly entete = viewChild<ElementRef<HTMLElement>>('entete'); // Sert à défiler le contenu de la page

  constructor() {
    // La page derrière le tiroir ne défile pas tant qu'il est ouvert
    effect(() => {
      this.document.body.style.overflow = this.menuOuvert() ? 'hidden' : ''; 
    });

    // L'en-tête collant masquerait le haut d'une section atteinte par un lien
    // (/#experts) : le défilement s'arrête juste sous l'en-tête
    const defilement = inject(ViewportScroller);
    defilement.setOffset(() => [0, (this.entete()?.nativeElement.offsetHeight ?? 0) + 16]);
    inject(DestroyRef).onDestroy(() => defilement.setOffset([0, 0]));
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
