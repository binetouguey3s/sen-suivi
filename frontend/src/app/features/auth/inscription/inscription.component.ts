import { ChangeDetectionStrategy, Component, effect, untracked, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService, ErreurFormulaire } from '../../../core/services/auth.service';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { LayoutAuthComponent } from '../../../shared/layout-auth/layout-auth.component';

@Component({
  selector: 'ss-inscription',
  standalone: true,
  imports: [RouterLink, ChampComponent, IconComponent, LayoutAuthComponent],
  templateUrl: './inscription.component.html',
  styleUrl: './inscription.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InscriptionComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly prenom = signal('');
  protected readonly nom = signal('');
  protected readonly email = signal('');
  protected readonly motDePasse = signal('');
  protected readonly conditions = signal(false);
  protected readonly enCours = signal(false);
  protected readonly erreurs = signal<Record<string, string>>({});

  // Force du mot de passe : 1 (faible) à 3 (solide), affichée en trois segments.
  protected readonly force = computed(() => {
    const mdp = this.motDePasse();
    if (!mdp) return 0;
    let points = 0;
    if (mdp.length >= 8) points++;
    if (/[A-Z]/.test(mdp) && /[a-z]/.test(mdp)) points++;
    if (/\d/.test(mdp) && /[^A-Za-z0-9]/.test(mdp)) points++;
    return Math.max(1, points);
  });

  constructor() {
    // Une erreur disparaît dès que l'utilisateur corrige un champ.
    effect(() => {
      this.prenom(); this.nom(); this.email(); this.motDePasse(); this.conditions();
      untracked(() => this.erreurs.set({}));
    });
  }

  protected async valider(evenement: Event): Promise<void> {
    evenement.preventDefault();
    const erreurs: Record<string, string> = {};
    if (!this.prenom().trim()) erreurs['prenom'] = 'Indiquez votre prénom.';
    if (!this.nom().trim()) erreurs['nom'] = 'Indiquez votre nom.';
    if (!/^\S+@\S+\.\S+$/.test(this.email())) erreurs['email'] = 'Indiquez une adresse e-mail valide.';
    if (this.motDePasse().length < 8) erreurs['password'] = 'Le mot de passe doit contenir au moins 8 caractères.';
    if (!this.conditions()) erreurs['conditions'] = "Acceptez les conditions d'utilisation pour continuer.";
    this.erreurs.set(erreurs);
    if (Object.keys(erreurs).length) return;

    this.enCours.set(true);
    try {
      await this.auth.inscrireUtilisateur({
        prenom: this.prenom().trim(),
        nom: this.nom().trim(),
        email: this.email().trim(),
        password: this.motDePasse(),
      });
      await this.auth.connecter(this.email().trim(), this.motDePasse());
      await this.router.navigateByUrl('/bienvenue');
    } catch (erreur) {
      this.erreurs.set(erreur instanceof ErreurFormulaire ? erreur.champs : { general: (erreur as Error).message });
    } finally {
      this.enCours.set(false);
    }
  }
}
