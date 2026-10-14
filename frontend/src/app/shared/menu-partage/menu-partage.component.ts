import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';

import { IconComponent } from '../icon/icon.component';

// Largeur du menu, hauteur estimée avant le premier affichage, et marge au
// bord de l'écran, pour le placer près de son bouton
const LARGEUR_MENU = 248;
const HAUTEUR_MENU = 260;
const MARGE = 12;
// Durée d'affichage de « Lien copié »
const DUREE_ANNONCE = 2500;

let compteur = 0;

// Menu de partage d'une ressource (ss-menu-partage) : copier le lien, WhatsApp,
// e-mail, enregistrer en PDF (impression du navigateur), et sur mobile le
// partage natif. Une seule instance par page ; chaque bouton « Partager »
// l'ouvre avec basculer(bouton) et lit son état avec ouvertPour(bouton).
// Popover sous le bouton sur ordinateur, feuille en bas d'écran sur mobile.
@Component({
  selector: 'ss-menu-partage',
  standalone: true,
  imports: [IconComponent],
  template: `
    <p class="mp__annonce" role="status">{{ annonce() }}</p>
    @if (declencheur()) {
      <div class="mp__voile" (click)="fermer(true)"></div>
      <div
        #menu
        class="mp"
        role="menu"
        aria-label="Partager cette ressource"
        [id]="identifiant"
        [style.top.px]="position()?.top"
        [style.left.px]="position()?.left"
        (keydown)="clavier($event)"
      >
        @if (partageNatif) {
          <button type="button" class="mp__item" role="menuitem" (click)="partagerNatif()">
            <ss-icon nom="plus-options" taille="sm" /> Plus d’options…
          </button>
        }
        <button type="button" class="mp__item" role="menuitem" (click)="copier()">
          <ss-icon nom="lien" taille="sm" /> Copier le lien
        </button>
        <a class="mp__item" role="menuitem" [href]="lienWhatsapp()" target="_blank" rel="noopener noreferrer" (click)="fermer(true)">
          <ss-icon nom="chat" taille="sm" /> WhatsApp
        </a>
        <a class="mp__item" role="menuitem" [href]="lienCourriel()" (click)="fermer(true)">
          <ss-icon nom="courriel" taille="sm" /> E-mail
        </a>
        <button type="button" class="mp__item" role="menuitem" (click)="imprimer()">
          <ss-icon nom="pdf" taille="sm" /> Enregistrer en PDF
        </button>
      </div>
    }
  `,
  styleUrl: './menu-partage.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:click)': 'clicExterieur($event)',
    '(window:resize)': 'fermer(false)',
    '(window:scroll)': 'fermer(false)',
  },
})
export class MenuPartageComponent {
  private readonly injector = inject(Injector);
  private readonly menu = viewChild<ElementRef<HTMLElement>>('menu');

  readonly titre = input.required<string>();
  // Adresse propre de la ressource (/ressources/:id), sans paramètres ni ancre
  readonly url = input.required<string>();

  readonly identifiant = `menu-partage-${++compteur}`;
  // Sur mobile seulement : la feuille de partage du système
  protected readonly partageNatif =
    typeof navigator.share === 'function' && !!globalThis.matchMedia?.('(pointer: coarse)').matches;

  // Bouton qui a ouvert le menu (null : fermé) ; le focus y revient à la fermeture
  protected readonly declencheur = signal<HTMLElement | null>(null);
  protected readonly position = signal<{ top: number; left: number } | null>(null);
  protected readonly annonce = signal('');
  private minuterie: ReturnType<typeof setTimeout> | undefined;

  protected readonly lienWhatsapp = computed(
    () => `https://wa.me/?text=${encodeURIComponent(`${this.titre()} — une ressource bien-être Sen Suivi : ${this.url()}`)}`,
  );
  protected readonly lienCourriel = computed(() => {
    const corps =
      `Bonjour,\n\nVoici une ressource bien-être de Sen Suivi qui pourrait vous intéresser : ` +
      `« ${this.titre()} ».\n\n${this.url()}`;
    return `mailto:?subject=${encodeURIComponent(this.titre())}&body=${encodeURIComponent(corps)}`;
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.minuterie));
  }

  ouvertPour(bouton: HTMLElement): boolean {
    return this.declencheur() === bouton;
  }

  basculer(bouton: HTMLElement): void {
    if (this.declencheur() === bouton) {
      this.fermer(true);
      return;
    }
    this.declencheur.set(bouton);
    this.position.set(this.placer(bouton, HAUTEUR_MENU));
    afterNextRender(
      () => {
        // Placement définitif avec la vraie hauteur du menu, puis le focus va
        // sur le premier choix, comme dans un menu natif
        const hauteur = this.menu()?.nativeElement.offsetHeight;
        if (hauteur) this.position.set(this.placer(bouton, hauteur));
        this.items()[0]?.focus();
      },
      { injector: this.injector },
    );
  }

  // Ordinateur : sous le bouton, aligné à droite, sans sortir de l'écran.
  // Mobile : pas de position, la feuille est collée en bas de l'écran.
  // Sous le bouton s'il y a la place, sinon juste au-dessus.
  private placer(bouton: HTMLElement, hauteur: number): { top: number; left: number } | null {
    if (globalThis.matchMedia?.('(max-width: 599px)').matches) return null;
    const cadre = bouton.getBoundingClientRect();
    const left = Math.max(MARGE, Math.min(cadre.right - LARGEUR_MENU, window.innerWidth - LARGEUR_MENU - MARGE));
    const dessous = cadre.bottom + 8;
    const top = dessous + hauteur > window.innerHeight - MARGE ? Math.max(MARGE, cadre.top - 8 - hauteur) : dessous;
    return { top, left };
  }

  fermer(rendreFocus: boolean): void {
    const bouton = this.declencheur();
    if (!bouton) return;
    this.declencheur.set(null);
    if (rendreFocus) bouton.focus();
  }

  protected clicExterieur(evenement: MouseEvent): void {
    const cible = evenement.target as Node | null;
    if (!this.declencheur() || !cible) return;
    if (this.menu()?.nativeElement.contains(cible) || this.declencheur()!.contains(cible)) return;
    this.fermer(false);
  }

  // Flèches, Début et Fin parcourent les choix ; Échap ferme et rend le focus au bouton
  protected clavier(evenement: KeyboardEvent): void {
    const items = this.items();
    const actuel = items.indexOf(document.activeElement as HTMLElement);
    const aller = (i: number) => items[(i + items.length) % items.length]?.focus();
    switch (evenement.key) {
      case 'ArrowDown':
        aller(actuel + 1);
        break;
      case 'ArrowUp':
        aller(actuel - 1);
        break;
      case 'Home':
        aller(0);
        break;
      case 'End':
        aller(items.length - 1);
        break;
      case 'Escape':
        this.fermer(true);
        break;
      case 'Tab':
        this.fermer(false);
        return;
      default:
        return;
    }
    evenement.preventDefault();
  }

  private items(): HTMLElement[] {
    return [...(this.menu()?.nativeElement.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])];
  }

  protected async copier(): Promise<void> {
    this.fermer(true);
    try {
      await navigator.clipboard.writeText(this.url());
      this.annoncer('Lien copié');
    } catch {
      this.annoncer('Le lien n’a pas pu être copié.');
    }
  }

  protected async partagerNatif(): Promise<void> {
    this.fermer(true);
    try {
      await navigator.share({ title: this.titre(), url: this.url() });
    } catch {
      // partage annulé par l'utilisateur : rien à faire
    }
  }

  // « Enregistrer au format PDF » de la boîte d'impression : le titre du
  // document devient le nom du fichier proposé, puis il est restauré
  protected imprimer(): void {
    this.fermer(true);
    const avant = document.title;
    document.title = `${this.titre()} — Sen Suivi`;
    window.addEventListener('afterprint', () => (document.title = avant), { once: true });
    window.print();
  }

  private annoncer(texte: string): void {
    this.annonce.set(texte);
    clearTimeout(this.minuterie);
    this.minuterie = setTimeout(() => this.annonce.set(''), DUREE_ANNONCE);
  }
}
