import { ChangeDetectionStrategy, Component, computed, inject, output } from '@angular/core';
import { RouterLink } from '@angular/router';

import { IconComponent } from '../../../shared/icon/icon.component';
import { BIEN_ETRE, Choix, DUREES, PREOCCUPATIONS } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

function libelle(liste: readonly Choix[], valeur: string): string {
  return liste.find((c) => c.valeur === valeur)?.libelle ?? valeur;
}

// Écran final : ce que Titou a retenu, et trois premières ressources
@Component({
  selector: 'ss-etape-pret',
  standalone: true,
  imports: [IconComponent, RouterLink],
  template: `
    <h1 class="ob-titre" tabindex="-1">Ton parcours est prêt{{ store.prenom() ? ', ' + store.prenom() : '' }}&nbsp;!</h1>
    <p class="ob-sous-titre">Voici ce que Titou a retenu pour toi.</p>

    <section class="ob-section ob-carte profil">
      <div class="profil__entete">
        <strong><ss-icon nom="suggestion" taille="sm" /> Ton profil bien-être</strong>
        <button type="button" (click)="modifier.emit()">Modifier</button>
      </div>
      @if (etiquettes().length) {
        <ul>
          @for (e of etiquettes(); track e) {
            <li>{{ e }}</li>
          }
        </ul>
      } @else {
        <p class="ob-aide">Tu n’as rien indiqué : Titou te proposera des contenus variés pour commencer.</p>
      }
    </section>

    <section class="ob-section">
      <p class="ob-question">Pour commencer</p>
      <ul class="suggestions">
        @for (s of store.suggestions(); track s.titre) {
          <li>
            <a class="suggestion" routerLink="/ressources">
              <img [src]="s.image" alt="" loading="lazy" />
              <strong>{{ s.titre }}</strong>
              <small>{{ s.meta }}</small>
            </a>
          </li>
        }
      </ul>
    </section>

    <a class="pause" routerLink="/ressources">
      <span>
        <small>Ta première pause</small>
        2 minutes de respiration guidée, maintenant&nbsp;?
      </span>
      <span class="pause__lecture" aria-hidden="true"><ss-icon nom="lecture" taille="sm" /></span>
    </a>
  `,
  styleUrl: './etapes.scss',
  styles: `
    .profil__entete {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .profil__entete strong {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
    }
    .profil__entete button {
      border: none;
      background: none;
      color: var(--ss-texte-marque);
      font-size: 12px;
      font-weight: var(--ss-poids-titre);
      cursor: pointer;
    }
    .profil ul {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .profil li {
      padding: 4px 10px;
      border: 1px solid var(--ss-bordure);
      border-radius: var(--ss-rayon-pilule);
      background: var(--ss-surface-legere);
      font-size: 11px;
      font-weight: var(--ss-poids-texte-fort);
    }
    .suggestions {
      display: flex;
      gap: 12px;
      margin: 0 calc(-1 * var(--ss-marge-mobile));
      padding: 0 var(--ss-marge-mobile) 6px;
      overflow-x: auto;
      list-style: none;
      scroll-snap-type: x mandatory;
      // Dès la tablette, les trois cartes se partagent toute la largeur
      @media (min-width: 600px) {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        margin: 0;
        padding: 0 0 6px;
        overflow: visible;
      }
    }
    .suggestions li {
      flex: none;
      width: 150px;
      scroll-snap-align: start;
      @media (min-width: 600px) {
        width: auto;
      }
    }
    .suggestion {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 6px 6px 10px;
      border: 1px solid var(--ss-bordure);
      border-radius: 14px;
      background: var(--ss-surface);
      color: var(--ss-texte);
      text-decoration: none;
      box-shadow: var(--ss-ombre);
    }
    .suggestion img {
      width: 100%;
      height: 76px;
      margin-bottom: 6px;
      @media (min-width: 900px) {
        height: auto;
        aspect-ratio: 16 / 10;
      }
      object-fit: cover;
      border-radius: 10px;
    }
    .suggestion strong {
      padding: 0 4px;
      font-size: 12px;
      line-height: 1.3;
    }
    .suggestion small {
      padding: 0 4px;
      font-size: 11px;
      color: var(--ss-texte-doux);
    }
    .pause {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: var(--ss-espace-3);
      padding: 14px 16px;
      border-radius: 16px;
      background: linear-gradient(120deg, #2f7d7a, #1b4b6e);
      color: #ffffff;
      font-size: 14px;
      font-weight: var(--ss-poids-titre);
      text-decoration: none;
      box-shadow: var(--ss-ombre-forte);
    }
    .pause small {
      display: block;
      font-size: 11px;
      font-weight: var(--ss-poids-texte);
      opacity: 0.85;
    }
    .pause__lecture {
      display: grid;
      place-items: center;
      flex: none;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.18);
      border: 1px solid rgba(255, 255, 255, 0.35);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapePretComponent {
  protected readonly store = inject(OnboardingStore);
  readonly modifier = output<void>();

  // Résumé lisible : préoccupations, envies, durée et rappels
  protected readonly etiquettes = computed(() => {
    const s = this.store;
    const resume = [
      ...s.preoccupations().map((v) => libelle(PREOCCUPATIONS, v)),
      ...s.bienEtre().map((v) => libelle(BIEN_ETRE, v)),
    ];
    const duree = s.duree();
    if (duree) resume.push(`${libelle(DUREES, duree)} par jour`);
    if (s.rappels() && s.frequenceRappels() !== 'jamais') {
      resume.push(s.frequenceRappels() === 'quotidien' ? 'Rappels chaque jour' : 'Rappels 3× / semaine');
    }
    return resume;
  });
}
