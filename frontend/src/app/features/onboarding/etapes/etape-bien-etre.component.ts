import { ChangeDetectionStrategy, Component, ElementRef, inject, signal, viewChild } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { BIEN_ETRE, SPIRITUALITE } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 4 : ce qui fait du bien. « Spiritualité et prière » ouvre un choix plus fin.
@Component({
  selector: 'ss-etape-bien-etre',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="entete">
      <h1 class="ob-titre" tabindex="-1">Qu’est-ce qui vous fait du bien&nbsp;?</h1>
      @if (store.bienEtre().length) {
        <span class="compteur"><ss-icon nom="coche" taille="sm" /> {{ store.bienEtre().length }} choix</span>
      }
    </div>
    <p class="ob-sous-titre">Choisissez tout ce qui vous parle. Vous pourrez le modifier à tout moment.</p>

    <div class="ob-section tuiles" role="group" aria-label="Ce qui vous fait du bien">
      @for (b of activites; track b.valeur) {
        @let choisi = store.bienEtre().includes(b.valeur);
        <button type="button" class="tuile" [attr.aria-pressed]="choisi" (click)="basculer(b.valeur)">
          <span class="tuile__icone"><ss-icon [nom]="b.icone!" taille="md" /></span>
          <span class="tuile__libelle">{{ b.libelle }}</span>
          @if (choisi) {
            <span class="tuile__coche" aria-hidden="true"><ss-icon nom="coche" taille="sm" /></span>
          }
        </button>
      }
    </div>

    @if (feuilleOuverte()) {
      <div class="voile" (click)="fermer()"></div>
      <div
        #feuille
        class="feuille"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ob-spi-titre"
        tabindex="-1"
        (keydown.escape)="fermer()"
      >
        <span class="feuille__poignee" aria-hidden="true"></span>
        <div class="feuille__entete">
          <span class="tuile__icone"><ss-icon nom="spiritualite" taille="md" /></span>
          <div>
            <h2 id="ob-spi-titre">Spiritualité et prière</h2>
            <p>Qu’est-ce qui vous apaise le plus&nbsp;?</p>
          </div>
        </div>
        <div class="ob-puces">
          @for (s of spiritualite; track s.valeur) {
            @let choisi = store.spiritualite().includes(s.valeur);
            <button type="button" class="ob-puce" [attr.aria-pressed]="choisi" (click)="store.basculer(store.spiritualite, s.valeur)">
              @if (choisi) { <ss-icon nom="coche" taille="sm" /> }
              {{ s.libelle }}
            </button>
          }
        </div>
        <p class="ob-note feuille__note">
          <ss-icon nom="cadenas" taille="sm" />
          Facultatif. Sert uniquement à vous proposer des contenus apaisants qui vous ressemblent.
        </p>
        <button type="button" class="feuille__valider" (click)="fermer()">
          Valider{{ store.spiritualite().length ? ' · ' + store.spiritualite().length + ' choix' : '' }}
          <ss-icon nom="fleche" taille="sm" />
        </button>
      </div>
    }
  `,
  styleUrl: './etapes.scss',
  styles: `
    @use 'verre' as *;

    .entete {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    .compteur {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex: none;
      margin-top: 6px;
      padding: 3px 10px;
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-surface-accent);
      color: var(--ss-texte-marque);
      font-size: 12px;
      font-weight: var(--ss-poids-titre);
    }
    .tuiles {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      @media (min-width: 900px) {
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }
    }
    .tuile {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      min-height: 84px;
      padding: 10px 6px;
      border: 1.5px solid var(--ss-bordure);
      border-radius: 16px;
      background: var(--ss-surface);
      color: var(--ss-texte);
      cursor: pointer;
    }
    .tuile[aria-pressed='true'] {
      border-color: var(--ss-primaire);
      box-shadow: var(--ss-ombre);
    }
    .tuile__icone {
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--ss-surface-legere);
      color: var(--ss-texte-marque);
    }
    .tuile[aria-pressed='true'] .tuile__icone {
      background: var(--ss-primaire);
      color: var(--ss-primaire-texte);
    }
    .tuile__libelle {
      font-size: 11px;
      font-weight: var(--ss-poids-texte-fort);
      line-height: 1.2;
      text-align: center;
    }
    .tuile__coche {
      position: absolute;
      top: -6px;
      right: -6px;
      display: grid;
      place-items: center;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--ss-accent);
      color: var(--ss-accent-texte);
    }
    .voile {
      position: fixed;
      inset: 0;
      z-index: 10;
      background: var(--ss-voile);
      animation: apparition var(--ss-duree) var(--ss-ease);
    }
    .feuille {
      @include ss-verre(20px);
      position: fixed;
      z-index: 11;
      left: 0;
      right: 0;
      bottom: 0;
      max-width: 480px;
      margin: 0 auto;
      padding: 10px 20px calc(24px + env(safe-area-inset-bottom));
      border-radius: 24px 24px 0 0;
      animation: montee var(--ss-duree) var(--ss-ease);
      outline: none;
      @media (min-width: 900px) {
        top: 50%;
        bottom: auto;
        max-width: 420px;
        padding-top: 20px;
        padding-bottom: 20px;
        border-radius: 24px;
        transform: translateY(-50%);
        animation: apparition var(--ss-duree) var(--ss-ease);
      }
    }
    .feuille__poignee {
      display: block;
      width: 40px;
      height: 4px;
      margin: 0 auto 14px;
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-bordure);
      @media (min-width: 900px) {
        display: none;
      }
    }
    .feuille__entete {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }
    .feuille__entete h2 {
      font-size: 17px;
      color: var(--ss-verre-texte);
    }
    .feuille__entete p {
      margin: 0;
      font-size: 12px;
      color: var(--ss-texte-doux);
    }
    .feuille__note {
      padding: 10px 12px;
      border-radius: 12px;
      background: var(--ss-surface-legere);
    }
    .feuille__valider {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      width: 100%;
      min-height: 48px;
      margin-top: 16px;
      border: none;
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-primaire);
      color: var(--ss-primaire-texte);
      font-size: 15px;
      font-weight: var(--ss-poids-titre);
      cursor: pointer;
    }
    @keyframes montee {
      from {
        transform: translateY(100%);
      }
    }
    @keyframes apparition {
      from {
        opacity: 0;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .voile,
      .feuille {
        animation: none;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeBienEtreComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly activites = BIEN_ETRE;
  protected readonly spiritualite = SPIRITUALITE;
  protected readonly feuilleOuverte = signal(false);
  private readonly feuille = viewChild<ElementRef<HTMLElement>>('feuille');
  private declencheur: HTMLElement | null = null;

  protected basculer(valeur: string): void {
    const ajout = !this.store.bienEtre().includes(valeur);
    this.store.basculer(this.store.bienEtre, valeur);
    if (valeur === 'spiritualite' && ajout) this.ouvrir();
  }

  private ouvrir(): void {
    this.declencheur = document.activeElement as HTMLElement | null;
    this.feuilleOuverte.set(true);
    queueMicrotask(() => setTimeout(() => this.feuille()?.nativeElement.focus()));
  }

  protected fermer(): void {
    this.feuilleOuverte.set(false);
    this.declencheur?.focus();
  }
}
