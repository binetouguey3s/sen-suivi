import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { Ressource, StatutRessource } from '../../../core/models/suivi';
import { AuthService } from '../../../core/services/auth.service';
import { RessourcesProService } from '../../../core/services/ressources-pro.service';
import { valeurs } from '../../../core/utils/ressource';
import { CarteRessourceComponent } from '../../../shared/carte-ressource/carte-ressource.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { ORDRE_STATUTS, STATUTS, dateDeLigne, format, initiales } from './ressources-pro';

type Filtre = StatutRessource | 'TOUTES';

interface ProfilPro {
  nom: string;
  specialite_affichee: string;
  ville: string;
}

// « Mes ressources » (/pro/ressources) : ce que le professionnel a proposé,
// par statut, avec les actions possibles à chaque étape de la relecture.
@Component({
  selector: 'ss-mes-ressources',
  standalone: true,
  imports: [RouterLink, IconComponent, ModalComponent, CarteRessourceComponent],
  templateUrl: './mes-ressources.component.html',
  styleUrl: './mes-ressources.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MesRessourcesComponent {
  private readonly auth = inject(AuthService);
  protected readonly service = inject(RessourcesProService);

  protected readonly ressources = httpResource<Ressource[]>(() => {
    this.service.version();
    return `${API_BASE_URL}/pro/ressources`;
  }, { defaultValue: [] });
  protected readonly profil = httpResource<ProfilPro>(() => {
    const id = this.auth.identifiant();
    return id ? `${API_BASE_URL}/professionnels/${id}` : undefined;
  });

  protected readonly statuts = STATUTS;
  protected readonly format = format;
  protected readonly dateDeLigne = dateDeLigne;
  protected readonly initiales = initiales;

  protected readonly liste = computed(() => valeurs(this.ressources));
  protected readonly nombre = (statut: StatutRessource) => this.liste().filter((r) => r.statut === statut).length;
  protected readonly onglets = computed(() => [
    { valeur: 'TOUTES' as Filtre, libelle: 'Toutes', nombre: this.liste().length },
    ...ORDRE_STATUTS.map((s) => ({ valeur: s as Filtre, libelle: STATUTS[s].onglet, nombre: this.nombre(s) })),
  ]);
  protected readonly filtre = signal<Filtre>('TOUTES');
  protected readonly visibles = computed(() =>
    this.filtre() === 'TOUTES' ? this.liste() : this.liste().filter((r) => r.statut === this.filtre()),
  );

  protected readonly nomAffiche = computed(() => (this.profil.hasValue() ? this.profil.value().nom : (this.auth.nom() ?? '')));
  protected readonly specialite = computed(() => (this.profil.hasValue() ? this.profil.value().specialite_affichee : ''));
  protected readonly ville = computed(() => (this.profil.hasValue() ? this.profil.value().ville : ''));

  // Actions : aperçu, lien copié, suppression confirmée
  protected readonly apercu = signal<Ressource | null>(null);
  protected readonly aSupprimer = signal<Ressource | null>(null);
  protected readonly suppressionEnCours = signal(false);
  protected readonly annonce = signal('');
  protected readonly erreur = signal<string | null>(null);

  constructor() {
    // Le message de soumission ne s'affiche qu'une fois
    inject(DestroyRef).onDestroy(() => this.service.soumissionReussie.set(false));
  }

  protected async copierLien(r: Ressource): Promise<void> {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/ressources/${r.id}`);
      this.annonce.set('Lien copié');
    } catch {
      this.annonce.set('Le lien n’a pas pu être copié.');
    }
    setTimeout(() => this.annonce.set(''), 2500);
  }

  protected async supprimer(): Promise<void> {
    const r = this.aSupprimer();
    if (!r) return;
    this.suppressionEnCours.set(true);
    this.erreur.set(null);
    try {
      await this.service.supprimer(r.id);
      this.aSupprimer.set(null);
    } catch {
      this.erreur.set('La suppression a échoué. Réessayez dans un instant.');
    } finally {
      this.suppressionEnCours.set(false);
    }
  }

  protected ouvertSuppression(ouverte: boolean): void {
    if (!ouverte) this.aSupprimer.set(null);
  }

  protected ouvertApercu(ouverte: boolean): void {
    if (!ouverte) this.apercu.set(null);
  }
}
