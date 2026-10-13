import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';

import { IconComponent } from '../../shared/icon/icon.component';
import { ECRANS, ETAPES, Ecran, ORDRE } from './onboarding.donnees';
import { OnboardingStore } from './onboarding.store';
import { EtapeAccompagnementComponent } from './etapes/etape-accompagnement.component';
import { EtapeBienEtreComponent } from './etapes/etape-bien-etre.component';
import { EtapeEspritComponent } from './etapes/etape-esprit.component';
import { EtapeHumeurComponent } from './etapes/etape-humeur.component';
import { EtapeIntroComponent } from './etapes/etape-intro.component';
import { EtapePretComponent } from './etapes/etape-pret.component';
import { EtapeProfilComponent } from './etapes/etape-profil.component';
import { EtapeRythmeComponent } from './etapes/etape-rythme.component';
import { EtapeSplashComponent } from './etapes/etape-splash.component';

// Onboarding de personnalisation, affiché juste après l'inscription (/bienvenue).
// Écran d'accueil visuel, présentation, six étapes facultatives, puis le parcours
// prêt. Mobile : photo en bandeau au-dessus du contenu. Desktop (≥ 900 px) :
// panneau photo fixe à gauche, contenu à droite.
@Component({
  selector: 'ss-onboarding',
  standalone: true,
  imports: [
    IconComponent,
    EtapeSplashComponent,
    EtapeIntroComponent,
    EtapeProfilComponent,
    EtapeHumeurComponent,
    EtapeEspritComponent,
    EtapeBienEtreComponent,
    EtapeRythmeComponent,
    EtapeAccompagnementComponent,
    EtapePretComponent,
  ],
  providers: [OnboardingStore],
  templateUrl: './onboarding.component.html',
  styleUrl: './onboarding.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingComponent {
  private readonly router = inject(Router);
  protected readonly store = inject(OnboardingStore);

  private readonly titre = viewChild<ElementRef<HTMLElement>>('contenu');

  protected readonly etapes = ETAPES;
  protected readonly ecran = signal<Ecran>('splash');
  protected readonly info = computed(() => ECRANS[this.ecran()]);
  // Numéro d'étape de 1 à 6, 0 hors des étapes (accueil, présentation, final)
  protected readonly numero = computed(() => ETAPES.indexOf(this.ecran()) + 1);
  protected readonly enEtape = computed(() => this.numero() > 0);
  protected readonly annonce = signal('');

  protected readonly libelleBouton = computed(() => {
    switch (this.ecran()) {
      case 'splash':
        return 'Commencer';
      case 'intro':
        return 'C’est parti';
      case 'accompagnement':
        return 'Créer mon parcours';
      case 'pret':
        return 'Découvrir mon espace';
      default:
        return 'Continuer';
    }
  });

  constructor() {
    // À chaque écran : remonter en haut et placer le focus sur le contenu,
    // pour que le lecteur d'écran lise le nouveau titre
    effect(() => {
      this.ecran();
      const contenu = this.titre()?.nativeElement;
      if (!contenu) return;
      queueMicrotask(() => {
        contenu.scrollTo?.({ top: 0 });
        globalThis.scrollTo?.({ top: 0 });
        contenu.querySelector<HTMLElement>('h1')?.focus({ preventScroll: true });
      });
    });
  }

  protected async suivant(): Promise<void> {
    const ecran = this.ecran();
    if (ecran === 'pret') {
      await this.router.navigateByUrl('/app');
      return;
    }
    if (ecran === 'accompagnement') {
      // Les réponses ne partent qu'une fois, à la fin des six étapes
      if (!(await this.store.enregistrer('termine'))) return;
    }
    this.aller(ORDRE[ORDRE.indexOf(ecran) + 1]);
  }

  protected precedent(): void {
    const i = ORDRE.indexOf(this.ecran());
    if (i > 0) this.aller(ORDRE[i - 1]);
  }

  // « Passer » : on garde ce qui a déjà été répondu, puis on entre dans l'espace
  protected async passer(): Promise<void> {
    await this.store.enregistrer('passe');
    await this.router.navigateByUrl('/app');
  }

  protected aller(ecran: Ecran): void {
    this.ecran.set(ecran);
    const n = ETAPES.indexOf(ecran) + 1;
    this.annonce.set(n > 0 ? `Étape ${n} sur ${ETAPES.length}` : '');
  }
}
