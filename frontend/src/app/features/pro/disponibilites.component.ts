import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';

import { FicheProfessionnelService } from '../../core/services/fiche-professionnel.service';
import { IconComponent } from '../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../shared/interrupteur/interrupteur.component';

// Disponibilité du professionnel : il peut suspendre les nouvelles demandes
// (congés, agenda complet). Il reste visible dans l'annuaire, mais
// l'algorithme d'orientation ne le suggère plus et aucune demande n'arrive.
@Component({
  selector: 'ss-disponibilites',
  standalone: true,
  imports: [IconComponent, InterrupteurComponent],
  template: `
    <header class="dispo__entete">
      <h1>Disponibilités</h1>
    </header>
    <section class="dispo__carte">
      <span class="dispo__icone" aria-hidden="true"><ss-icon nom="calendrier" taille="lg" /></span>
      @if (chargement()) {
        <p>Chargement…</p>
      } @else {
        <div class="dispo__option">
          <div>
            <h2>J'accepte de nouvelles demandes</h2>
            <p>
              @if (accepte()) {
                Les utilisateurs peuvent vous envoyer une demande de mise en relation, et Sen Suivi peut vous suggérer à ceux dont le besoin correspond à vos domaines.
              } @else {
                Vous restez visible dans l'annuaire, mais vous ne recevez plus de nouvelles demandes et n'êtes plus suggéré. Les demandes déjà reçues restent dans votre espace.
              }
            </p>
          </div>
          <ss-interrupteur libelle="J'accepte de nouvelles demandes" [actif]="accepte()" (actifChange)="basculer($event)" />
        </div>
        @if (erreur()) { <p class="dispo__erreur" role="alert">{{ erreur() }}</p> }
      }
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
        color: var(--ss-texte-marque);

        @media (min-width: 900px) {
          font-size: 42px;
          letter-spacing: var(--ss-interlettrage-grand);
        }
      }

      .dispo__carte {
        margin-top: var(--ss-espace-4);
        padding: var(--ss-espace-4) var(--ss-espace-3);
        background: var(--ss-surface);
        border-radius: var(--ss-rayon-grande-carte);
        box-shadow: var(--ss-ombre);
      }

      .dispo__icone {
        display: inline-flex;
        padding: var(--ss-espace-2);
        border-radius: 50%;
        background: var(--ss-surface-douce);
        color: var(--ss-texte-marque);
      }

      .dispo__option {
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: center;
        gap: var(--ss-espace-3);
        margin-top: var(--ss-espace-3);
      }

      h2 {
        margin: 0;
        font-family: var(--ss-police-titres);
        font-weight: var(--ss-poids-titre);
        font-size: 20px;
        color: var(--ss-texte);
      }

      p {
        margin: var(--ss-espace-1) 0 0;
        color: var(--ss-texte-doux);
      }

      .dispo__erreur {
        color: var(--ss-texte);
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DisponibilitesComponent {
  private readonly fiche = inject(FicheProfessionnelService);

  protected readonly chargement = signal(true);
  protected readonly accepte = signal(true);
  protected readonly erreur = signal<string | null>(null);

  constructor() {
    void this.charger();
  }

  private async charger(): Promise<void> {
    try {
      this.accepte.set((await this.fiche.charger()).accepte_demandes);
    } catch {
      this.erreur.set('Impossible de charger votre disponibilité. Réessayez dans un instant.');
    } finally {
      this.chargement.set(false);
    }
  }

  protected async basculer(valeur: boolean): Promise<void> {
    const avant = this.accepte();
    this.accepte.set(valeur);
    this.erreur.set(null);
    try {
      await this.fiche.modifier({ accepte_demandes: valeur });
    } catch {
      this.accepte.set(avant);
      this.erreur.set("L'enregistrement a échoué. Réessayez dans un instant.");
    }
  }
}
