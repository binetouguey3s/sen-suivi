import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { IconComponent } from '../../shared/icon/icon.component';
import { CourbeMarqueComponent } from '../../shared/courbe-marque/courbe-marque.component';

@Component({
  selector: 'ss-page-404',
  standalone: true,
  imports: [RouterLink, IconComponent, CourbeMarqueComponent],
  template: `
    <section class="e404">
      <p class="e404__chiffre" aria-hidden="true">404</p>
      <ss-courbe-marque class="e404__courbe" />
      <h1>Cette page n'existe pas</h1>
      <p class="e404__texte">Le lien est peut-être ancien ou mal recopié.</p>
      <a class="e404__bouton" routerLink="/">Retour à l'accueil</a>
      <a class="e404__lien" routerLink="/chatbot">Parler au chatbot <ss-icon nom="fleche" taille="sm" /></a>
    </section>
  `,
  styles: [
    `
      .e404 { position: relative; display: flex; flex-direction: column; align-items: center; gap: var(--ss-espace-2); text-align: center; padding: var(--ss-espace-8) var(--ss-marge-mobile); overflow: hidden; }
      .e404__chiffre { position: absolute; top: var(--ss-espace-3); margin: 0; font-family: var(--ss-police-titres); font-weight: var(--ss-poids-titre-fort); font-size: 200px; line-height: 1; color: var(--ss-menthe-pale); z-index: 0; }
      .e404__courbe { position: relative; width: 100%; height: 90px; margin-bottom: var(--ss-espace-4); }
      h1 { position: relative; font-size: 34px; color: var(--ss-bleu-profond); }
      .e404__texte { position: relative; margin: 0; color: var(--ss-gris-ardoise); font-size: 17px; }
      .e404__bouton { position: relative; background: var(--ss-bleu-sen-suivi); color: var(--ss-blanc); border-radius: var(--ss-rayon-bouton); padding: var(--ss-espace-2) var(--ss-espace-4); font-weight: var(--ss-poids-texte-fort); text-decoration: none; box-shadow: var(--ss-ombre-carte); margin-top: var(--ss-espace-2); }
      .e404__lien { position: relative; display: inline-flex; align-items: center; gap: var(--ss-espace-1); color: var(--ss-bleu-sen-suivi); text-decoration: none; font-weight: var(--ss-poids-texte-fort); }
      @media (min-width: 900px) { h1 { font-size: 52px; } .e404__chiffre { font-size: 320px; } }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Page404Component {}
