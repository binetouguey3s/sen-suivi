import { DOCUMENT } from '@angular/common';
import { HttpClient, HttpErrorResponse, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, computed, effect, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
import { EtatAcces, MoyenPaiement, ProfessionnelPublic } from '../../core/models/orientation';
import { AccesService } from '../../core/services/acces.service';
import { AuthService } from '../../core/services/auth.service';
import { UrgenceService } from '../../core/services/urgence.service';
import { BadgeOffreComponent } from '../../shared/badge-offre/badge-offre.component';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalComponent } from '../../shared/modal/modal.component';

const MOYENS_PAIEMENT: { valeur: MoyenPaiement; libelle: string }[] = [
  { valeur: 'WAVE', libelle: 'Wave' },
  { valeur: 'ORANGE_MONEY', libelle: 'Orange Money' },
  { valeur: 'FREE_MONEY', libelle: 'Free Money' },
];

// Fiche d'un professionnel. Deux contextes : /professionnels/:id (fiche
// publique, vue par un utilisateur) et /pro/profil (le professionnel
// consulte sa propre fiche dans son espace, sans :id).
@Component({
  selector: 'ss-profil-professionnel',
  standalone: true,
  imports: [RouterLink, BadgeOffreComponent, ChampComponent, IconComponent, ModalComponent],
  templateUrl: './profil.component.html',
  styleUrl: './profil.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfilProfessionnelComponent {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);
  private readonly acces = inject(AccesService);
  // Détresse détectée par le chatbot : ni tarif, ni compteur, ni écran de paiement
  protected readonly enDetresse = inject(UrgenceService).enDetresse;

  // Paramètre de route :id (withComponentInputBinding), absent sur /pro/profil
  readonly id = input<string>();

  private readonly identifiant = computed(() => this.id() ?? String(this.auth.identifiant() ?? ''));
  protected readonly pro = httpResource<ProfessionnelPublic>(() => `${API_BASE_URL}/professionnels/${this.identifiant()}`);

  protected readonly peutDemander = computed(() => this.auth.typeCompte() === 'utilisateur');
  protected readonly estMaFiche = computed(
    () => this.auth.typeCompte() === 'professionnel' && String(this.auth.identifiant()) === this.identifiant(),
  );
  protected readonly demandeOuverte = signal(false);
  protected readonly confirmationOuverte = signal(false);
  protected readonly message = signal('');
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);

  // Écran de déblocage : seulement après l'offre de lancement, jamais en détresse
  protected readonly deblocageOuvert = signal(false);
  protected readonly etatAcces = signal<EtatAcces | null>(null);
  protected readonly moyens = MOYENS_PAIEMENT;
  protected readonly moyen = signal<MoyenPaiement>('WAVE');
  protected readonly telephone = signal('');
  protected readonly paiementEnCours = signal(false);
  protected readonly messagePaiement = signal<string | null>(null);
  protected readonly tarifAcces = computed(() => (this.etatAcces()?.tarif_fcfa ?? 0).toLocaleString('fr-FR'));

  protected readonly portrait = computed(() => {
    const p = this.pro.value();
    return p ? (IMAGE_PAR_PROFESSIONNEL[p.nom] ?? null) : null;
  });
  protected readonly initiales = computed(() =>
    (this.pro.value()?.nom ?? '').split(' ').slice(0, 2).map((m) => m[0]).join('').toUpperCase(),
  );
  protected readonly langues = computed(() =>
    (this.pro.value()?.langue ?? '')
      .split(',')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => l.charAt(0).toUpperCase() + l.slice(1)),
  );
  protected readonly tarif = computed(() => `${Math.round(this.pro.value()?.tarif_indicatif ?? 0).toLocaleString('fr-FR')} FCFA`);
  protected readonly aDesModalites = computed(() => {
    const p = this.pro.value();
    return !!p && (p.consultation_cabinet || p.consultation_distance);
  });

  constructor() {
    // Sur mobile, la barre « Demander une mise en relation » est fixée en bas :
    // on relève la bulle de chat du layout public pour qu'elle reste au-dessus.
    const racine = inject(DOCUMENT).documentElement;
    effect(() => {
      if (this.peutDemander() && this.pro.hasValue()) racine.style.setProperty('--ss-chat-decalage', '104px');
      else racine.style.removeProperty('--ss-chat-decalage');
    });
    inject(DestroyRef).onDestroy(() => racine.style.removeProperty('--ss-chat-decalage'));
  }

  // Avant d'ouvrir le formulaire : l'offre est-elle terminée ? Sinon, rien ne change.
  protected async ouvrirDemande(): Promise<void> {
    if (!this.enDetresse()) {
      try {
        const etat = await this.acces.etat();
        this.etatAcces.set(etat);
        if (etat.verrouille) {
          this.deblocageOuvert.set(true);
          return;
        }
      } catch {
        // État indisponible : le serveur tranchera à l'envoi
      }
    }
    this.demandeOuverte.set(true);
  }

  protected async payer(): Promise<void> {
    this.paiementEnCours.set(true);
    const resultat = await this.acces.payer(this.moyen(), this.telephone().trim());
    this.messagePaiement.set(resultat.message);
    this.paiementEnCours.set(false);
  }

  protected async envoyer(): Promise<void> {
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      await firstValueFrom(
        this.http.post(`${API_BASE_URL}/demandes-contact`, { professionnel: Number(this.identifiant()), message: this.message().trim() }),
      );
      this.demandeOuverte.set(false);
      this.message.set('');
      this.confirmationOuverte.set(true);
    } catch (e) {
      if (e instanceof HttpErrorResponse && e.status === 402) {
        // Offre terminée entre-temps : écran de déblocage, la demande n'est pas partie
        this.demandeOuverte.set(false);
        this.etatAcces.set(await this.acces.etat().catch(() => null));
        this.deblocageOuvert.set(true);
      } else {
        const detail = e instanceof HttpErrorResponse ? e.error?.professionnel?.[0] : null;
        this.erreur.set(detail ?? "L'envoi a échoué. Réessayez dans un instant.");
      }
    } finally {
      this.envoiEnCours.set(false);
    }
  }

  protected async retourAccueil(): Promise<void> {
    await this.router.navigateByUrl(this.auth.espaceAccueil());
  }
}
