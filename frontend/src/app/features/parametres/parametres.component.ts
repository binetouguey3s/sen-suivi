import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { VILLES_SENEGAL } from '../../core/models/comptes';
import { AuthService, ErreurFormulaire } from '../../core/services/auth.service';
import { Compte, CompteService } from '../../core/services/compte.service';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../shared/interrupteur/interrupteur.component';
import { ModalComponent } from '../../shared/modal/modal.component';

const NOTIFICATIONS = [
  { cle: 'rappel_journal', titre: 'Rappel du journal', texte: 'Un rappel doux pour compléter votre suivi quotidien.' },
  { cle: 'reponse_professionnel', titre: 'Réponse d’un professionnel', texte: 'Dès qu’un professionnel répond à votre demande.' },
  { cle: 'reponse_forum', titre: 'Réponse sur le forum', texte: 'Quand quelqu’un répond à votre publication.' },
  { cle: 'nouvelles_ressources', titre: 'Nouvelles ressources', texte: 'Articles et conseils adaptés à votre profil.' },
] as const;

@Component({
  selector: 'ss-parametres',
  standalone: true,
  imports: [ChampComponent, IconComponent, InterrupteurComponent, ModalComponent],
  templateUrl: './parametres.component.html',
  styleUrl: './parametres.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ParametresComponent {
  private readonly service = inject(CompteService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly villes = VILLES_SENEGAL;
  protected readonly notifications = NOTIFICATIONS;
  protected readonly compte = this.service.compte;
  protected readonly estUtilisateur = computed(() => this.compte()?.type_compte === 'utilisateur');

  protected readonly prenom = signal('');
  protected readonly nom = signal('');
  protected readonly email = signal('');
  protected readonly ville = signal('');
  protected readonly erreurs = signal<Record<string, string>>({});
  protected readonly infoEnregistre = signal(false);

  protected readonly ancien = signal('');
  protected readonly nouveau = signal('');
  protected readonly erreursMdp = signal<Record<string, string>>({});
  protected readonly mdpModifie = signal(false);

  protected readonly suppressionOuverte = signal(false);
  protected readonly mdpSuppression = signal('');
  protected readonly erreurSuppression = signal<string | null>(null);

  protected readonly chargement = signal(true);
  protected readonly erreurChargement = signal(false);

  constructor() {
    void this.charger();
  }

  private async charger(): Promise<void> {
    try {
      const c = await this.service.charger();
      this.remplir(c);
    } catch {
      this.erreurChargement.set(true);
    } finally {
      this.chargement.set(false);
    }
  }

  private remplir(c: Compte): void {
    this.prenom.set(c.prenom ?? '');
    this.nom.set(c.nom);
    this.email.set(c.email);
    this.ville.set(c.ville ?? '');
  }

  protected actif(cle: string, canal: 'email' | 'push'): boolean {
    return this.compte()?.preferences?.[cle]?.[canal] ?? true;
  }

  protected async basculer(cle: string, canal: 'email' | 'push', valeur: boolean): Promise<void> {
    const c = this.compte();
    if (!c) return;
    const preferences = { ...c.preferences, [cle]: { email: this.actif(cle, 'email'), push: this.actif(cle, 'push'), [canal]: valeur } };
    this.service.compte.set({ ...c, preferences });
    try {
      await this.service.modifier({ preferences });
    } catch {
      this.service.compte.set(c);
    }
  }

  protected async enregistrer(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.infoEnregistre.set(false);
    const e: Record<string, string> = {};
    if (this.estUtilisateur() && !this.prenom().trim()) e['prenom'] = 'Indiquez votre prénom.';
    if (!this.nom().trim()) e['nom'] = 'Indiquez votre nom.';
    if (!/^\S+@\S+\.\S+$/.test(this.email())) e['email'] = 'Indiquez une adresse e-mail valide.';
    this.erreurs.set(e);
    if (Object.keys(e).length) return;
    try {
      const donnees: Parameters<CompteService['modifier']>[0] = { nom: this.nom().trim(), email: this.email().trim(), ville: this.ville() };
      if (this.estUtilisateur()) donnees.prenom = this.prenom().trim();
      await this.service.modifier(donnees);
      this.infoEnregistre.set(true);
    } catch (err) {
      this.erreurs.set(err instanceof ErreurFormulaire ? err.champs : {});
    }
  }

  protected async changerMotDePasse(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.mdpModifie.set(false);
    if (this.nouveau().length < 8) {
      this.erreursMdp.set({ nouveau: 'Le mot de passe doit contenir au moins 8 caractères.' });
      return;
    }
    try {
      await this.service.changerMotDePasse(this.ancien(), this.nouveau());
      this.ancien.set('');
      this.nouveau.set('');
      this.erreursMdp.set({});
      this.mdpModifie.set(true);
    } catch (err) {
      this.erreursMdp.set(err instanceof ErreurFormulaire ? err.champs : {});
    }
  }

  protected async supprimer(): Promise<void> {
    this.erreurSuppression.set(null);
    try {
      await this.service.supprimer(this.mdpSuppression());
    } catch (err) {
      this.erreurSuppression.set(err instanceof ErreurFormulaire ? Object.values(err.champs)[0] : 'Suppression impossible.');
    }
  }

  protected async deconnecter(): Promise<void> {
    this.auth.deconnecter();
    await this.router.navigateByUrl('/');
  }
}
