import {
  ChangeDetectionStrategy,
  Component,
  DOCUMENT,
  ElementRef,
  OnDestroy,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';

import { IconComponent } from '../../shared/icon/icon.component';

const ETAPES = [
  {
    titre: 'Notez votre humeur en dix secondes',
    texte: 'Un suivi quotidien qui permet de voir évoluer son ressenti dans la durée.',
    image: '/images/illustrations/onboarding-1-humeur.svg',
  },
  {
    titre: "Un chatbot à l'écoute, sans jugement",
    texte: "L'échange est confidentiel. Le chatbot ne remplace jamais un professionnel de santé.",
    image: '/images/illustrations/onboarding-2-chatbot.svg',
  },
  {
    titre: 'Des professionnels près de chez vous, à Dakar comme en région',
    texte: 'Accédez à un réseau de psychologues, sophrologues et coachs validés pour un accompagnement sur mesure.',
    image: '/images/illustrations/onboarding-3-professionnels.svg',
  },
];

// Durées en miroir de onboarding.component.scss (--ss-duree = 320ms)
const DUREE = 320;
const DUREE_SORTIE = DUREE * 0.75;
const DUREE_VISUEL = 420;
const DUREE_CASCADE = 4 * 80 + DUREE; // 5 éléments espacés de 80 ms

// Balayage tactile
const SEUIL_BALAYAGE = 60; // px à parcourir pour changer d'étape
const SEUIL_INTENTION = 10; // px avant de savoir si le geste est horizontal ou vertical
const RESISTANCE_BORD = 0.35; // freine le glissement quand il n'y a pas d'étape de ce côté
const DELAI_CLIC_FANTOME = 300; // ms pendant lesquelles un clic suivant un balayage est ignoré

type Phase = 'repos' | 'entree' | 'sortie';
type Sens = 'aucun' | 'avant' | 'arriere';

interface Glissement {
  pointeur: number;
  departX: number;
  departY: number;
  dx: number;
  horizontal: boolean;
}

// navigator.connection n'est pas encore typé par TypeScript
interface ConnexionReseau extends EventTarget {
  saveData?: boolean;
}

function mouvementReduit(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function connexion(): ConnexionReseau | undefined {
  return (navigator as Navigator & { connection?: ConnexionReseau }).connection;
}

@Component({
  selector: 'ss-onboarding',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './onboarding.component.html',
  styleUrl: './onboarding.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[class.sans-animation]': 'sansAnimation()',
    '[class.economie-donnees]': 'economieDonnees()',
  },
})
export class OnboardingComponent implements OnDestroy {
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);

  private readonly carte = viewChild.required<ElementRef<HTMLElement>>('carte');
  private readonly illustration = viewChild.required<ElementRef<HTMLElement>>('illustration');
  private readonly texte = viewChild.required<ElementRef<HTMLElement>>('texte');
  private readonly titre = viewChild.required<ElementRef<HTMLElement>>('titre');

  protected readonly etapes = ETAPES;
  protected readonly index = signal(0);
  protected readonly etape = computed(() => ETAPES[this.index()]);
  protected readonly derniere = computed(() => this.index() === ETAPES.length - 1);

  protected readonly sansAnimation = signal(mouvementReduit());
  protected readonly economieDonnees = signal(connexion()?.saveData === true);
  protected readonly phase = signal<Phase>(this.sansAnimation() ? 'repos' : 'entree');
  protected readonly sens = signal<Sens>('aucun');
  protected readonly annonce = signal('');
  private readonly enTransition = signal(false);

  // Un seul AbortController retire d'un coup tous les écouteurs à la destruction
  private readonly ecouteurs = new AbortController();
  private readonly minuteries = new Set<ReturnType<typeof setTimeout>>();
  private image: number | null = null;
  private glissement: Glissement | null = null;
  private finBalayage = -Infinity;

  constructor() {
    if (this.phase() === 'entree') {
      this.planifier(() => this.phase.set('repos'), DUREE_CASCADE);
    }
    afterNextRender(() => this.brancherEcouteurs());
  }

  ngOnDestroy(): void {
    this.ecouteurs.abort();
    this.annulerMinuteries();
    if (this.image !== null) cancelAnimationFrame(this.image);
  }

  protected async suivant(): Promise<void> {
    if (this.derniere()) {
      await this.terminer();
    } else {
      this.aller(this.index() + 1);
    }
  }

  protected async terminer(): Promise<void> {
    await this.router.navigateByUrl('/app');
  }

  // ─── Changement d'étape ────────────────────────────────────────────────────

  private aller(cible: number): void {
    if (this.enTransition() || cible === this.index() || cible < 0 || cible >= ETAPES.length) return;

    if (this.sansAnimation()) {
      this.changerEtape(cible);
      return;
    }

    // Sortie, puis changement de contenu, puis entrée en cascade
    this.annulerMinuteries();
    this.enTransition.set(true);
    this.sens.set(cible > this.index() ? 'avant' : 'arriere');
    this.phase.set('sortie');

    this.planifier(() => {
      this.changerEtape(cible);
      this.phase.set('entree');
      this.planifier(() => this.enTransition.set(false), DUREE_VISUEL);
      this.planifier(() => this.phase.set('repos'), DUREE_CASCADE);
    }, DUREE_SORTIE);
  }

  private changerEtape(cible: number): void {
    this.index.set(cible);
    this.carte().nativeElement.classList.remove('ob--retour');
    for (const el of this.cibles()) {
      el.style.removeProperty('transform');
      el.style.removeProperty('--ob-depart');
    }
    this.annonce.set(`Étape ${cible + 1} sur ${ETAPES.length}`);
    this.titre().nativeElement.focus({ preventScroll: true });
  }

  // ─── Écouteurs ─────────────────────────────────────────────────────────────

  private brancherEcouteurs(): void {
    const options = { signal: this.ecouteurs.signal };
    const carte = this.carte().nativeElement;

    carte.addEventListener('pointerdown', (e) => this.debutGlissement(e), options);
    carte.addEventListener('pointermove', (e) => this.suiviGlissement(e), { ...options, passive: true });
    carte.addEventListener('pointerup', (e) => this.finGlissement(e), options);
    carte.addEventListener('pointercancel', () => this.annulerGlissement(), options);
    // Un balayage qui se termine sur le bouton ne doit pas aussi le cliquer
    carte.addEventListener('click', (e) => this.bloquerClicFantome(e), { ...options, capture: true });

    this.document.addEventListener('keydown', (e) => this.clavier(e), options);

    if (typeof matchMedia === 'function') {
      matchMedia('(prefers-reduced-motion: reduce)').addEventListener(
        'change',
        (e) => this.sansAnimation.set(e.matches),
        options,
      );
    }
    connexion()?.addEventListener(
      'change',
      () => this.economieDonnees.set(connexion()?.saveData === true),
      options,
    );

    // Précharge les illustrations suivantes : en 3G, l'image est prête avant son entrée
    for (const etape of ETAPES.slice(1)) {
      new Image().src = etape.image;
    }
  }

  private clavier(e: KeyboardEvent): void {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      this.aller(this.index() + 1);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      this.aller(this.index() - 1);
    }
  }

  private bloquerClicFantome(e: Event): void {
    if (performance.now() - this.finBalayage < DELAI_CLIC_FANTOME) {
      e.stopPropagation();
      e.preventDefault();
    }
  }

  // ─── Balayage tactile ──────────────────────────────────────────────────────

  private debutGlissement(e: PointerEvent): void {
    if (e.pointerType === 'mouse' || this.enTransition() || this.glissement) return;
    this.glissement = { pointeur: e.pointerId, departX: e.clientX, departY: e.clientY, dx: 0, horizontal: false };
  }

  private suiviGlissement(e: PointerEvent): void {
    const g = this.glissement;
    if (!g || e.pointerId !== g.pointeur) return;

    const dx = e.clientX - g.departX;
    const dy = e.clientY - g.departY;

    if (!g.horizontal) {
      // Geste vertical : on laisse la page défiler
      if (Math.abs(dy) > SEUIL_INTENTION && Math.abs(dy) > Math.abs(dx)) {
        this.glissement = null;
        return;
      }
      if (Math.abs(dx) < SEUIL_INTENTION) return;
      g.horizontal = true;
      const carte = this.carte().nativeElement;
      carte.setPointerCapture?.(e.pointerId);
      carte.classList.add('ob--glisse');
    }

    g.dx = dx;
    // Au plus une écriture dans le DOM par image affichée
    this.image ??= requestAnimationFrame(() => this.peindreGlissement());
  }

  private peindreGlissement(): void {
    this.image = null;
    if (!this.glissement) return;
    const transform = `translateX(${this.decalage(this.glissement.dx)}px)`;
    for (const el of this.cibles()) el.style.transform = transform;
  }

  private finGlissement(e: PointerEvent): void {
    const g = this.glissement;
    if (!g || e.pointerId !== g.pointeur) return;
    this.glissement = null;
    this.annulerImage();
    this.carte().nativeElement.classList.remove('ob--glisse');
    if (!g.horizontal) return;

    this.finBalayage = performance.now();
    const cible =
      g.dx <= -SEUIL_BALAYAGE ? this.index() + 1 : g.dx >= SEUIL_BALAYAGE ? this.index() - 1 : null;

    if (cible !== null && cible >= 0 && cible < ETAPES.length) {
      // La sortie repart de l'endroit où le doigt a lâché le contenu
      for (const el of this.cibles()) el.style.setProperty('--ob-depart', `${this.decalage(g.dx)}px`);
      this.aller(cible);
    } else {
      this.retourElastique();
    }
  }

  private annulerGlissement(): void {
    const g = this.glissement;
    this.glissement = null;
    this.annulerImage();
    this.carte().nativeElement.classList.remove('ob--glisse');
    if (g?.horizontal) this.retourElastique();
  }

  private retourElastique(): void {
    const carte = this.carte().nativeElement;
    carte.classList.add('ob--retour');
    for (const el of this.cibles()) el.style.removeProperty('transform');
    this.planifier(() => carte.classList.remove('ob--retour'), DUREE);
  }

  // Freine le glissement vers un côté où il n'y a pas d'étape
  private decalage(dx: number): number {
    const bord = (dx > 0 && this.index() === 0) || (dx < 0 && this.derniere());
    return bord ? dx * RESISTANCE_BORD : dx;
  }

  // ─── Utilitaires ───────────────────────────────────────────────────────────

  private cibles(): HTMLElement[] {
    return [this.illustration().nativeElement, this.texte().nativeElement];
  }

  private planifier(action: () => void, delai: number): void {
    const id = setTimeout(() => {
      this.minuteries.delete(id);
      action();
    }, delai);
    this.minuteries.add(id);
  }

  private annulerMinuteries(): void {
    for (const id of this.minuteries) clearTimeout(id);
    this.minuteries.clear();
  }

  private annulerImage(): void {
    if (this.image !== null) {
      cancelAnimationFrame(this.image);
      this.image = null;
    }
  }
}
