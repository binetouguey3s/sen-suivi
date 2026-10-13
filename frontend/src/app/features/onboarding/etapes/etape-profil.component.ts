import { ChangeDetectionStrategy, Component, WritableSignal, inject } from '@angular/core';

import { IconComponent } from '../../../shared/icon/icon.component';
import { GENRES, LANGUES, SITUATIONS, TRANCHES_AGE } from '../onboarding.donnees';
import { OnboardingStore } from '../onboarding.store';

// Étape 1 : prénom d'usage, genre, âge, situation et langue
@Component({
  selector: 'ss-etape-profil',
  standalone: true,
  imports: [IconComponent],
  template: `
    <h1 class="ob-titre" tabindex="-1">Parlez-nous un peu de vous</h1>
    <p class="ob-sous-titre">Tout est facultatif. Ces infos adaptent le ton et les contenus.</p>

    <section class="ob-section">
      <label class="ob-question" for="ob-prenom">Comment souhaitez-vous qu’on vous appelle&nbsp;?</label>
      <div class="ob-champ">
        <ss-icon nom="utilisateur" taille="sm" />
        <input
          id="ob-prenom"
          type="text"
          autocomplete="given-name"
          maxlength="150"
          [value]="store.prenom()"
          (input)="store.prenom.set($any($event.target).value)"
        />
      </div>
      <p class="ob-aide">Votre vrai nom n’apparaît jamais sur le forum.</p>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-genre">Vous êtes…</p>
      <div class="ob-puces" role="radiogroup" aria-labelledby="ob-genre">
        @for (c of genres; track c.valeur) {
          <button type="button" class="ob-puce" role="radio" [attr.aria-checked]="store.genre() === c.valeur" (click)="choisir(store.genre, c.valeur)">
            @if (store.genre() === c.valeur) { <ss-icon nom="coche" taille="sm" /> }
            {{ c.libelle }}
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-age">Votre tranche d’âge</p>
      <div class="ob-puces" role="radiogroup" aria-labelledby="ob-age">
        @for (c of tranches; track c.valeur) {
          <button type="button" class="ob-puce" role="radio" [attr.aria-checked]="store.trancheAge() === c.valeur" (click)="choisir(store.trancheAge, c.valeur)">
            @if (store.trancheAge() === c.valeur) { <ss-icon nom="coche" taille="sm" /> }
            {{ c.libelle }}
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-situation">Votre situation</p>
      <div class="ob-puces" role="radiogroup" aria-labelledby="ob-situation">
        @for (c of situations; track c.valeur) {
          <button type="button" class="ob-puce" role="radio" [attr.aria-checked]="store.situation() === c.valeur" (click)="choisir(store.situation, c.valeur)">
            @if (store.situation() === c.valeur) { <ss-icon nom="coche" taille="sm" /> }
            {{ c.libelle }}
          </button>
        }
      </div>
    </section>

    <section class="ob-section">
      <p class="ob-question" id="ob-langue">Votre langue préférée</p>
      <div class="ob-puces" role="radiogroup" aria-labelledby="ob-langue">
        @for (c of langues; track c.valeur) {
          <button type="button" class="ob-puce" role="radio" [attr.aria-checked]="store.langue() === c.valeur" (click)="choisir(store.langue, c.valeur)">
            @if (store.langue() === c.valeur) { <ss-icon nom="coche" taille="sm" /> }
            {{ c.libelle }}
          </button>
        }
      </div>
    </section>
  `,
  styleUrl: './etapes.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EtapeProfilComponent {
  protected readonly store = inject(OnboardingStore);
  protected readonly genres = GENRES;
  protected readonly tranches = TRANCHES_AGE;
  protected readonly situations = SITUATIONS;
  protected readonly langues = LANGUES;

  // Un second clic sur la réponse choisie la retire : rien n'est imposé
  protected choisir(champ: WritableSignal<string | null>, valeur: string): void {
    champ.set(champ() === valeur ? null : valeur);
  }
}
