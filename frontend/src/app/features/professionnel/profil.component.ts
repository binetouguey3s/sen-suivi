import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { HttpClient } from '@angular/common/http';

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
}

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

  // Paramètre de route :id (withComponentInputBinding)
  readonly id = input.required<string>();

  protected readonly pro = httpResource<ProfessionnelPublic>(() => `${API_BASE_URL}/professionnels/${this.id()}`);

  protected readonly peutDemander = computed(() => this.auth.typeCompte() === 'utilisateur');
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

  protected async envoyer(): Promise<void> {
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      await firstValueFrom(
        this.http.post(`${API_BASE_URL}/demandes-contact`, { professionnel: Number(this.id()), message: this.message().trim() }),
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
