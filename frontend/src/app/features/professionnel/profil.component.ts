import { DOCUMENT } from '@angular/common';
import { HttpClient, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, computed, effect, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
import { AuthService } from '../../core/services/auth.service';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalComponent } from '../../shared/modal/modal.component';

interface ProfessionnelPublic {
  id: number;
  nom: string;
  specialite_affichee: string;
  ville: string;
  langue: string;
  tarif_indicatif: number;
  presentation: string;
  domaines: string[];
  consultation_cabinet: boolean;
  adresse_cabinet: string;
  consultation_distance: boolean;
}

// Fiche d'un professionnel. Deux contextes : /professionnels/:id (fiche
// publique, vue par un utilisateur) et /pro/profil (le professionnel
// consulte sa propre fiche dans son espace, sans :id).
@Component({
  selector: 'ss-profil-professionnel',
  standalone: true,
  imports: [RouterLink, ChampComponent, IconComponent, ModalComponent],
  templateUrl: './profil.component.html',
  styleUrl: './profil.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfilProfessionnelComponent {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

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
    } catch {
      this.erreur.set("L'envoi a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }

  protected async retourAccueil(): Promise<void> {
    await this.router.navigateByUrl(this.auth.espaceAccueil());
  }
}
