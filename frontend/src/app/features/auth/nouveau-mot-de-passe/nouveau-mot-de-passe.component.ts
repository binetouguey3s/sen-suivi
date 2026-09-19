import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService, ErreurFormulaire } from '../../../core/services/auth.service';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { LayoutAuthComponent } from '../../../shared/layout-auth/layout-auth.component';

@Component({
  selector: 'ss-nouveau-mot-de-passe',
  standalone: true,
  imports: [RouterLink, ChampComponent, LayoutAuthComponent],
  template: `
    <ss-layout-auth citation="Votre espace de sérénité, en toute discrétion.">
      <h1 class="nmp__titre">Choisir un nouveau mot de passe</h1>
      @if (termine()) {
        <p class="nmp__ok" role="status">Votre mot de passe a été modifié.</p>
        <a class="nmp__bouton nmp__bouton--lien" routerLink="/connexion">Se connecter</a>
      } @else {
        <form class="nmp__formulaire" (submit)="valider($event)" novalidate>
          <ss-champ libelle="Nouveau mot de passe" type="password" [(valeur)]="motDePasse" autocomplete="new-password" [erreur]="erreur()" />
          <ss-champ libelle="Confirmer le mot de passe" type="password" [(valeur)]="confirmation" autocomplete="new-password" />
          <button type="submit" class="nmp__bouton" [disabled]="enCours()">{{ enCours() ? 'Enregistrement…' : 'Enregistrer' }}</button>
        </form>
      }
    </ss-layout-auth>
  `,
  styles: [
    `
      .nmp__titre { font-size: 26px; color: var(--ss-bleu-sen-suivi); text-align: center; margin-bottom: var(--ss-espace-3); }
      .nmp__formulaire { display: flex; flex-direction: column; gap: var(--ss-espace-2); }
      .nmp__ok { text-align: center; color: var(--ss-bleu-sen-suivi); }
      .nmp__bouton { border: none; border-radius: var(--ss-rayon-bouton); background: var(--ss-bleu-sen-suivi); color: var(--ss-blanc); font-size: 15px; font-weight: var(--ss-poids-texte-fort); padding: var(--ss-espace-2); cursor: pointer; }
      .nmp__bouton:disabled { opacity: 0.6; }
      .nmp__bouton--lien { display: block; text-align: center; text-decoration: none; }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NouveauMotDePasseComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Paramètres d'URL (?uid=…&token=…) liés aux entrées du composant
  readonly uid = input<string>();
  readonly token = input<string>();

  protected readonly motDePasse = signal('');
  protected readonly confirmation = signal('');
  protected readonly enCours = signal(false);
  protected readonly termine = signal(false);
  protected readonly erreur = signal<string | null>(null);

  protected async valider(evenement: Event): Promise<void> {
    evenement.preventDefault();
    if (this.motDePasse().length < 8) {
      this.erreur.set('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }
    if (this.motDePasse() !== this.confirmation()) {
      this.erreur.set('Les deux mots de passe ne correspondent pas.');
      return;
    }
    this.enCours.set(true);
    try {
      await this.auth.confirmerReinitialisation(this.uid() ?? '', this.token() ?? '', this.motDePasse());
      this.termine.set(true);
    } catch (e) {
      this.erreur.set(e instanceof ErreurFormulaire ? (Object.values(e.champs)[0] ?? null) : null);
    } finally {
      this.enCours.set(false);
    }
  }
}
