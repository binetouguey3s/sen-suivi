import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { DestroyRef, Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core';

// Choix proposé à l'utilisateur ; « systeme » suit le réglage de l'appareil.
export type Theme = 'clair' | 'sombre' | 'systeme';
export type ThemeApplique = Exclude<Theme, 'systeme'>;

// Même clé que le script de index.html, qui pose le thème avant le premier rendu
export const CLE_THEME = 'ss_theme';
const REQUETE_SOMBRE = '(prefers-color-scheme: dark)';
// Durée pendant laquelle les transitions sont coupées à la bascule
const DUREE_SANS_TRANSITION = 200;

function estTheme(valeur: unknown): valeur is Theme {
  return valeur === 'clair' || valeur === 'sombre' || valeur === 'systeme';
}

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly navigateur = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly requeteSombre = this.navigateur ? this.document.defaultView?.matchMedia?.(REQUETE_SOMBRE) : undefined;

  private readonly choixInterne = signal<Theme>(this.lireChoix());
  private readonly systemeSombre = signal(this.requeteSombre?.matches ?? false);
  private minuterieTransition?: ReturnType<typeof setTimeout>;

  // Thème choisi par l'utilisateur
  readonly choix = this.choixInterne.asReadonly();
  // Thème réellement affiché, une fois « systeme » résolu
  readonly applique = computed<ThemeApplique>(() => {
    const choix = this.choixInterne();
    if (choix !== 'systeme') return choix;
    return this.systemeSombre() ? 'sombre' : 'clair';
  });

  constructor() {
    // Le réglage de l'appareil change en direct : on suit, sans recharger
    const suivreSysteme = (e: MediaQueryListEvent) => {
      this.systemeSombre.set(e.matches);
      if (this.choixInterne() === 'systeme') this.appliquer();
    };
    this.requeteSombre?.addEventListener?.('change', suivreSysteme);
    inject(DestroyRef).onDestroy(() => this.requeteSombre?.removeEventListener?.('change', suivreSysteme));

    this.appliquer(false);
  }

  choisir(theme: Theme): void {
    if (theme === this.choixInterne()) return;
    this.choixInterne.set(theme);
    this.enregistrerChoix(theme);
    this.appliquer();
  }

  private appliquer(sansTransition = true): void {
    if (!this.navigateur) return;
    const racine = this.document.documentElement;
    // Coupe les transitions le temps de la bascule : sinon chaque élément
    // anime sa couleur à son rythme et l'écran clignote.
    if (sansTransition) {
      racine.classList.add('sans-transition');
      clearTimeout(this.minuterieTransition);
      this.minuterieTransition = setTimeout(() => racine.classList.remove('sans-transition'), DUREE_SANS_TRANSITION);
    }
    racine.dataset['theme'] = this.applique();
    this.mettreAJourBarreEtat();
  }

  // Barre d'état mobile : même couleur que le fond, lue dans les tokens du thème appliqué
  private mettreAJourBarreEtat(): void {
    const couleur = getComputedStyle(this.document.documentElement).getPropertyValue('--ss-fond').trim();
    if (!couleur) return;
    this.document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]').forEach((meta) => {
      meta.content = couleur;
    });
  }

  // localStorage peut lever une exception (navigation privée, stockage bloqué) :
  // le thème fonctionne alors pour la session, sans être retenu.
  private lireChoix(): Theme {
    if (!this.navigateur) return 'systeme';
    try {
      const valeur = this.document.defaultView?.localStorage.getItem(CLE_THEME);
      return estTheme(valeur) ? valeur : 'systeme';
    } catch {
      return 'systeme';
    }
  }

  private enregistrerChoix(theme: Theme): void {
    if (!this.navigateur) return;
    try {
      this.document.defaultView?.localStorage.setItem(CLE_THEME, theme);
    } catch {
      // Stockage indisponible : le choix vaut pour la session en cours
    }
  }
}
