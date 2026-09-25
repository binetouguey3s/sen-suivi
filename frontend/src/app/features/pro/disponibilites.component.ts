import { ChangeDetectionStrategy, Component } from '@angular/core';

import { IconComponent } from '../../shared/icon/icon.component';

// Écran réservé : la gestion des créneaux n'existe pas encore côté back-end.
@Component({
  selector: 'ss-disponibilites',
  standalone: true,
  imports: [IconComponent],
  template: `
    <header class="dispo__entete">
      <h1>Disponibilités</h1>
    </header>
    <section class="dispo__carte">
      <span class="dispo__icone" aria-hidden="true"><ss-icon nom="calendrier" taille="lg" /></span>
      <h2>Cette fonctionnalité arrive bientôt</h2>
      <p>Vous pourrez indiquer ici vos créneaux disponibles pour les mises en relation.</p>
    </section>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      h1 {
        margin: 0;
        font-family: var(--ss-police-titres);
        font-weight: var(--ss-poids-texte-fort);
        font-size: 28px;
        letter-spacing: var(--ss-interlettrage-moyen);
        color: var(--ss-bleu-sen-suivi);

        @media (min-width: 900px) {
          font-size: 42px;
          letter-spacing: var(--ss-interlettrage-grand);
        }
      }

      .dispo__carte {
        margin-top: var(--ss-espace-4);
        padding: var(--ss-espace-5) var(--ss-espace-3);
        background: var(--ss-fond-carte);
        border-radius: var(--ss-rayon-grande-carte);
        box-shadow: var(--ss-ombre-carte);
        text-align: center;
      }

      .dispo__icone {
        display: inline-flex;
        padding: var(--ss-espace-2);
        border-radius: 50%;
        background: var(--ss-menthe-pale);
        color: var(--ss-bleu-sen-suivi);
      }

      h2 {
        margin: var(--ss-espace-2) 0 0;
        font-family: var(--ss-police-titres);
        font-weight: var(--ss-poids-titre);
        font-size: 20px;
        color: var(--ss-bleu-profond);
      }

      p {
        margin: var(--ss-espace-1) 0 0;
        color: var(--ss-gris-ardoise);
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DisponibilitesComponent {}
