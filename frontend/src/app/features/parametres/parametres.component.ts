import { ChangeDetectionStrategy, Component, Injector, afterNextRender, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { VILLES_SENEGAL } from '../../core/models/comptes';
import { AuthService, ErreurFormulaire } from '../../core/services/auth.service';
import { Compte, CompteService } from '../../core/services/compte.service';
import { FicheProfessionnel, FicheProfessionnelService } from '../../core/services/fiche-professionnel.service';
import { verifierMotDePasse } from '../../core/utils/mot-de-passe';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../shared/interrupteur/interrupteur.component';
import { ModalComponent } from '../../shared/modal/modal.component';

interface TypeNotification {
  cle: string;
  titre: string;
  texte: string;
}

const NOTIFICATIONS_UTILISATEUR: TypeNotification[] = [
  { cle: 'rappel_journal', titre: 'Rappel du journal', texte: 'Un rappel doux pour compléter votre suivi quotidien.' },
  { cle: 'reponse_professionnel', titre: 'Réponse d’un professionnel', texte: 'Dès qu’un professionnel répond à votre demande.' },
  { cle: 'reponse_forum', titre: 'Réponse sur le forum', texte: 'Quand quelqu’un répond à votre publication.' },
  { cle: 'nouvelles_ressources', titre: 'Nouvelles ressources', texte: 'Articles et conseils adaptés à votre profil.' },
];

// Envoyée par le workflow n8n « nouvelle-demande », qui respecte ce réglage
const NOTIFICATIONS_PROFESSIONNEL: TypeNotification[] = [
  {
    cle: 'nouvelle_demande',
    titre: 'Nouvelle demande de mise en relation',
    texte: 'Dès qu’un utilisateur vous envoie une demande.',
  },
];

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
  private readonly ficheService = inject(FicheProfessionnelService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly injector = inject(Injector);

  protected readonly villes = VILLES_SENEGAL;
  protected readonly compte = this.service.compte;
  protected readonly estUtilisateur = computed(() => this.compte()?.type_compte === 'utilisateur');
  protected readonly estProfessionnel = computed(() => this.compte()?.type_compte === 'professionnel');
  protected readonly notifications = computed(() =>
    this.estProfessionnel() ? NOTIFICATIONS_PROFESSIONNEL : NOTIFICATIONS_UTILISATEUR,
  );

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

  // Fiche publique (professionnel uniquement)
  protected readonly ficheVille = signal('');
  protected readonly ficheLangue = signal('');
  protected readonly ficheTarif = signal('');
  protected readonly fichePresentation = signal('');
  protected readonly ficheDomaines = signal('');
  protected readonly ficheCabinet = signal(false);
  protected readonly ficheAdresse = signal('');
  protected readonly ficheDistance = signal(false);
  protected readonly erreursFiche = signal<Record<string, string>>({});
  protected readonly ficheEnregistree = signal(false);

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
      if (c.type_compte === 'professionnel') this.remplirFiche(await this.ficheService.charger());
    } catch {
      this.erreurChargement.set(true);
    } finally {
      this.chargement.set(false);
      this.defilerVersAncre();
    }
  }

  // Lien « Modifier ma fiche » (/pro/parametres#fiche) : la section n'existe
  // qu'une fois le compte chargé, on y défile après ce rendu.
  private defilerVersAncre(): void {
    const ancre = this.route.snapshot.fragment;
    if (!ancre) return;
    afterNextRender(() => document.getElementById(ancre)?.scrollIntoView({ behavior: 'smooth' }), { injector: this.injector });
  }

  private remplir(c: Compte): void {
    this.prenom.set(c.prenom ?? '');
    this.nom.set(c.nom);
    this.email.set(c.email);
    this.ville.set(c.ville ?? '');
  }

  private remplirFiche(f: FicheProfessionnel): void {
    this.ficheVille.set(f.ville);
    this.ficheLangue.set(f.langue);
    this.ficheTarif.set(String(Math.round(f.tarif_indicatif)));
    this.fichePresentation.set(f.presentation);
    this.ficheDomaines.set(f.domaines.join(', '));
    this.ficheCabinet.set(f.consultation_cabinet);
    this.ficheAdresse.set(f.adresse_cabinet);
    this.ficheDistance.set(f.consultation_distance);
  }

  protected async enregistrerFiche(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.ficheEnregistree.set(false);
    const e: Record<string, string> = {};
    const tarif = Number(this.ficheTarif());
    if (!this.ficheVille().trim()) e['ville'] = 'Indiquez votre ville.';
    if (!this.ficheLangue().trim()) e['langue'] = 'Indiquez au moins une langue.';
    if (!this.ficheTarif().trim() || Number.isNaN(tarif) || tarif < 0) e['tarif_indicatif'] = 'Indiquez un tarif en FCFA.';
    if (this.ficheCabinet() && !this.ficheAdresse().trim()) e['adresse_cabinet'] = "Indiquez l'adresse du cabinet.";
    this.erreursFiche.set(e);
    if (Object.keys(e).length) return;
    try {
      const fiche = await this.ficheService.modifier({
        ville: this.ficheVille().trim(),
        langue: this.ficheLangue().trim(),
        tarif_indicatif: tarif,
        presentation: this.fichePresentation().trim(),
        domaines: this.ficheDomaines().split(',').map((d) => d.trim()).filter(Boolean),
        consultation_cabinet: this.ficheCabinet(),
        adresse_cabinet: this.ficheCabinet() ? this.ficheAdresse().trim() : '',
        consultation_distance: this.ficheDistance(),
      });
      this.remplirFiche(fiche);
      this.ficheEnregistree.set(true);
    } catch (err) {
      this.erreursFiche.set(err instanceof ErreurFormulaire ? err.champs : {});
    }
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
      const donnees: Parameters<CompteService['modifier']>[0] = { nom: this.nom().trim(), email: this.email().trim() };
      // La ville d'un professionnel (avec son quartier) se modifie dans sa fiche publique
      if (this.estUtilisateur()) {
        donnees.prenom = this.prenom().trim();
        donnees.ville = this.ville();
      }
      await this.service.modifier(donnees);
      this.infoEnregistre.set(true);
    } catch (err) {
      this.erreurs.set(err instanceof ErreurFormulaire ? err.champs : {});
    }
  }

  protected async changerMotDePasse(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.mdpModifie.set(false);
    const erreurMdp = verifierMotDePasse(this.nouveau());
    if (erreurMdp) {
      this.erreursMdp.set({ nouveau: erreurMdp });
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
