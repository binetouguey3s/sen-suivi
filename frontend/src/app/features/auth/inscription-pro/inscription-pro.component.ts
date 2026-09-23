import { ChangeDetectionStrategy, Component, effect, untracked, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { LANGUES_PRO, SPECIALITES_PRO, VILLES_SENEGAL } from '../../../core/models/comptes';
import { AuthService, ErreurFormulaire } from '../../../core/services/auth.service';
import { verifierMotDePasse } from '../../../core/utils/mot-de-passe';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { LayoutAuthComponent } from '../../../shared/layout-auth/layout-auth.component';
import { ModalComponent } from '../../../shared/modal/modal.component';

@Component({
  selector: 'ss-inscription-pro',
  standalone: true,
  imports: [RouterLink, ChampComponent, IconComponent, LayoutAuthComponent, ModalComponent],
  templateUrl: './inscription-pro.component.html',
  styleUrl: './inscription-pro.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InscriptionProComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly specialites = SPECIALITES_PRO;
  protected readonly villes = VILLES_SENEGAL;
  protected readonly languesDisponibles = LANGUES_PRO;

  protected readonly prenom = signal('');
  protected readonly nom = signal('');
  protected readonly email = signal('');
  protected readonly motDePasse = signal('');
  protected readonly specialite = signal('');
  protected readonly ville = signal('');
  protected readonly langues = signal<string[]>(['Français']);
  protected readonly tarif = signal('');
  protected readonly presentation = signal('');

  protected readonly enCours = signal(false);
  protected readonly erreurs = signal<Record<string, string>>({});
  protected readonly confirmation = signal(false);

  protected basculerLangue(langue: string): void {
    this.langues.update((l) => (l.includes(langue) ? l.filter((x) => x !== langue) : [...l, langue]));
  }

  constructor() {
    // Une erreur disparaît dès que l'utilisateur corrige un champ.
    effect(() => {
      this.prenom(); this.nom(); this.email(); this.motDePasse(); this.specialite(); this.ville(); this.langues(); this.tarif(); this.presentation();
      untracked(() => this.erreurs.set({}));
    });
  }

  protected async valider(evenement: Event): Promise<void> {
    evenement.preventDefault();
    const e: Record<string, string> = {};
    if (!this.prenom().trim()) e['prenom'] = 'Indiquez votre prénom.';
    if (!this.nom().trim()) e['nom'] = 'Indiquez votre nom.';
    if (!/^\S+@\S+\.\S+$/.test(this.email())) e['email'] = 'Indiquez une adresse e-mail valide.';
    const erreurMdp = verifierMotDePasse(this.motDePasse());
    if (erreurMdp) e['password'] = erreurMdp;
    if (!this.specialite()) e['specialite'] = 'Choisissez une spécialité.';
    if (!this.ville()) e['ville'] = 'Sélectionnez votre ville.';
    if (!this.langues().length) e['langue'] = 'Choisissez au moins une langue.';
    if (!(Number(this.tarif()) > 0)) e['tarif_indicatif'] = 'Indiquez un tarif indicatif en FCFA.';
    this.erreurs.set(e);
    if (Object.keys(e).length) return;

    this.enCours.set(true);
    try {
      await this.auth.inscrireProfessionnel({
        nom: `${this.prenom().trim()} ${this.nom().trim()}`,
        email: this.email().trim(),
        password: this.motDePasse(),
        specialite: this.specialite(),
        ville: this.ville(),
        langue: this.langues().join(', '),
        tarif_indicatif: Number(this.tarif()),
        presentation: this.presentation().trim(),
      });
      this.confirmation.set(true);
    } catch (erreur) {
      this.erreurs.set(erreur instanceof ErreurFormulaire ? erreur.champs : { general: (erreur as Error).message });
    } finally {
      this.enCours.set(false);
    }
  }

  protected async retourAccueil(): Promise<void> {
    await this.router.navigateByUrl('/');
  }
}
