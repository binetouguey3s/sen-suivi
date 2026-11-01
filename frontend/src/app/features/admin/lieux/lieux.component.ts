import { HttpErrorResponse, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { imageDuLieu } from '../../../core/config/images-lieux';
import { REGIONS } from '../../../core/config/lieux';
import { LieuDetente } from '../../../core/models/suivi';
import { AdministrationService } from '../../../core/services/administration.service';
import { valeurs } from '../../../core/utils/ressource';
import { CouvertureLieuComponent } from '../../../shared/couverture-lieu/couverture-lieu.component';
import { IconComponent } from '../../../shared/icon/icon.component';

type FiltrePhoto = 'SANS' | 'AVEC' | 'TOUTES';

// Mêmes règles que le serveur, pour répondre avant d'envoyer le fichier
const EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const TAILLE_MAX_MO = 5;

function sansAccents(texte: string): string {
  return texte.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

@Component({
  selector: 'ss-admin-lieux',
  standalone: true,
  imports: [RouterLink, IconComponent, CouvertureLieuComponent],
  templateUrl: './lieux.component.html',
  styleUrl: './lieux.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminLieuxComponent {
  private readonly administration = inject(AdministrationService);

  // Paramètres d'URL : la page d'un lieu ouvre directement ce lieu ici
  readonly q = input<string>();
  readonly photo = input<string>();

  protected readonly regions = REGIONS;
  protected readonly formats = EXTENSIONS.join(',');

  protected readonly recherche = linkedSignal(() => this.q() ?? '');
  protected readonly filtrePhoto = linkedSignal<FiltrePhoto>(() => {
    const p = this.photo();
    return p === 'AVEC' || p === 'TOUTES' ? p : 'SANS';
  });
  protected readonly region = signal('');

  protected readonly enCours = signal<number | null>(null);
  protected readonly confirmation = signal('');
  protected readonly erreur = signal<{ id: number; message: string } | null>(null);

  protected readonly lieux = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, { defaultValue: [] });

  protected readonly total = computed(() => valeurs(this.lieux).length);
  protected readonly nombreSansPhoto = computed(() => valeurs(this.lieux).filter((l) => !this.image(l)).length);

  protected readonly affiches = computed(() => {
    const filtre = this.filtrePhoto();
    const region = this.region();
    const mots = sansAccents(this.recherche()).split(/\s+/).filter(Boolean);
    return valeurs(this.lieux).filter((l) => {
      if (filtre === 'SANS' && this.image(l)) return false;
      if (filtre === 'AVEC' && !this.image(l)) return false;
      if (region && l.region !== region) return false;
      const texte = sansAccents(`${l.nom} ${l.ville} ${l.region}`);
      return mots.every((mot) => texte.includes(mot));
    });
  });

  protected image(lieu: LieuDetente): string | null {
    return imageDuLieu(lieu);
  }

  protected saisirRecherche(evenement: Event): void {
    this.recherche.set((evenement.target as HTMLInputElement).value);
  }

  protected choisirFiltre(evenement: Event): void {
    this.filtrePhoto.set((evenement.target as HTMLSelectElement).value as FiltrePhoto);
  }

  protected choisirRegion(evenement: Event): void {
    this.region.set((evenement.target as HTMLSelectElement).value);
  }

  protected async envoyer(lieu: LieuDetente, evenement: Event): Promise<void> {
    const champ = evenement.target as HTMLInputElement;
    const fichier = champ.files?.[0];
    if (!fichier) return;
    const refus = this.refus(fichier);
    if (refus) {
      this.signaler(lieu.id, refus);
    } else {
      await this.agir(lieu, () => this.administration.envoyerImageLieu(lieu.id, fichier), `Photo enregistrée pour ${lieu.nom}.`);
    }
    // Permet de choisir à nouveau le même fichier après une erreur
    if (champ.isConnected) champ.value = '';
  }

  protected retirer(lieu: LieuDetente): Promise<void> {
    return this.agir(lieu, () => this.administration.retirerImageLieu(lieu.id), `Photo retirée pour ${lieu.nom}.`);
  }

  private refus(fichier: File): string | null {
    const nom = fichier.name.toLowerCase();
    if (!EXTENSIONS.some((extension) => nom.endsWith(extension))) return 'Formats acceptés : JPEG, PNG ou WebP.';
    if (fichier.size > TAILLE_MAX_MO * 1024 * 1024) return `Le fichier dépasse ${TAILLE_MAX_MO} Mo.`;
    return null;
  }

  private async agir(lieu: LieuDetente, action: () => Promise<void>, message: string): Promise<void> {
    this.enCours.set(lieu.id);
    this.erreur.set(null);
    this.confirmation.set('');
    try {
      await action();
      this.confirmation.set(message);
      this.lieux.reload();
    } catch (e) {
      this.signaler(lieu.id, this.messageErreur(e));
    } finally {
      this.enCours.set(null);
    }
  }

  private signaler(id: number, message: string): void {
    this.confirmation.set('');
    this.erreur.set({ id, message });
  }

  private messageErreur(e: unknown): string {
    const corps = e instanceof HttpErrorResponse ? e.error : null;
    const detail = corps?.image?.[0] ?? corps?.detail;
    return typeof detail === 'string' ? detail : 'Envoi impossible pour le moment. Vérifiez votre connexion et réessayez.';
  }
}
