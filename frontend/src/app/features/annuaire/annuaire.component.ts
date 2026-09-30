import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
import { ProfessionnelPublic, SuggestionOrientation } from '../../core/models/orientation';
import { AuthService } from '../../core/services/auth.service';
import { BadgeOffreComponent } from '../../shared/badge-offre/badge-offre.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { PaginationComponent, tranche } from '../../shared/pagination/pagination.component';

const CLE_SUGGESTION_IGNOREE = 'sen-suivi.suggestion-ignoree';

function lireIgnoree(): number | null {
  try {
    return Number(sessionStorage.getItem(CLE_SUGGESTION_IGNOREE)) || null;
  } catch {
    return null;
  }
}

function premiereMajuscule(texte: string): string {
  return texte.charAt(0).toUpperCase() + texte.slice(1);
}

// Annuaire des professionnels. Pour un utilisateur connecté : UN professionnel
// mis en avant par l'algorithme d'orientation, avec la raison de ce choix,
// PUIS la liste complète, librement consultable et filtrable. La suggestion
// n'enferme jamais le choix, et l'ignorer ne demande aucune justification.
@Component({
  selector: 'ss-annuaire',
  standalone: true,
  imports: [RouterLink, IconComponent, BadgeOffreComponent, PaginationComponent],
  templateUrl: './annuaire.component.html',
  styleUrl: './annuaire.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AnnuaireComponent {
  private readonly auth = inject(AuthService);
  protected readonly estUtilisateur = computed(() => this.auth.typeCompte() === 'utilisateur');

  private readonly orientation = httpResource<SuggestionOrientation>(() =>
    this.estUtilisateur() ? `${API_BASE_URL}/orientation/suggestion` : undefined,
  );
  private readonly publics = httpResource<ProfessionnelPublic[]>(() =>
    this.estUtilisateur() ? undefined : `${API_BASE_URL}/professionnels/valides`,
  );

  protected readonly chargement = computed(() => this.orientation.isLoading() || this.publics.isLoading());
  protected readonly erreur = computed(() => !!this.orientation.error() || !!this.publics.error());

  private readonly tous = computed<ProfessionnelPublic[]>(() => {
    if (this.orientation.hasValue()) return this.orientation.value().professionnels;
    return this.publics.hasValue() ? this.publics.value() : [];
  });

  private readonly ignoree = signal<number | null>(lireIgnoree());
  protected readonly suggestion = computed(() => {
    const s = this.orientation.hasValue() ? this.orientation.value().suggestion : null;
    return s && s.professionnel.id !== this.ignoree() ? s : null;
  });

  // Filtres, construits à partir des valeurs réellement présentes
  protected readonly specialite = signal<string | null>(null);
  protected readonly ville = signal('');
  protected readonly langue = signal('');
  protected readonly aDistance = signal(false);
  protected readonly enCabinet = signal(false);
  protected readonly recherche = signal('');

  protected readonly specialites = computed(() =>
    [...new Set(this.tous().map((p) => p.specialite_affichee))].sort((a, b) => a.localeCompare(b, 'fr')),
  );
  protected readonly villes = computed(() =>
    [...new Set(this.tous().map((p) => p.ville.split(/\s+/)[0]))].sort((a, b) => a.localeCompare(b, 'fr')),
  );
  protected readonly langues = computed(() =>
    [...new Set(this.tous().flatMap((p) => this.languesDe(p)))].sort((a, b) => a.localeCompare(b, 'fr')),
  );

  protected readonly professionnels = computed(() => {
    const texte = this.recherche().trim().toLowerCase();
    return this.tous().filter(
      (p) =>
        (!this.specialite() || p.specialite_affichee === this.specialite()) &&
        (!this.ville() || p.ville.startsWith(this.ville())) &&
        (!this.langue() || this.languesDe(p).includes(this.langue())) &&
        (!this.aDistance() || p.consultation_distance) &&
        (!this.enCabinet() || p.consultation_cabinet) &&
        (!texte || `${p.nom} ${p.specialite_affichee} ${p.domaines.join(' ')}`.toLowerCase().includes(texte)),
    );
  });

  // Pagination : retour à la première page quand les filtres changent
  protected readonly page = linkedSignal({ source: () => [this.specialite(), this.ville(), this.langue(), this.aDistance(), this.enCabinet(), this.recherche()], computation: () => 1 });
  protected readonly professionnelsPage = computed(() => tranche(this.professionnels(), this.page(), 9));
  protected readonly filtresActifs = computed(
    () => !!(this.specialite() || this.ville() || this.langue() || this.aDistance() || this.enCabinet() || this.recherche()),
  );

  protected languesDe(p: ProfessionnelPublic): string[] {
    return p.langue
      .split(/[,/;]| et /)
      .map((l) => premiereMajuscule(l.trim().toLowerCase()))
      .filter(Boolean);
  }

  protected portrait(p: { nom: string }): string | null {
    return IMAGE_PAR_PROFESSIONNEL[p.nom] ?? null;
  }

  protected initiales(nom: string): string {
    return nom.split(/\s+/).slice(0, 2).map((m) => m[0]).join('').toUpperCase();
  }

  protected ignorer(id: number): void {
    this.ignoree.set(id);
    try {
      sessionStorage.setItem(CLE_SUGGESTION_IGNOREE, String(id));
    } catch {
      // Stockage indisponible : la suggestion reste masquée pour cette visite
    }
  }

  protected effacerFiltres(): void {
    this.specialite.set(null);
    this.ville.set('');
    this.langue.set('');
    this.aDistance.set(false);
    this.enCabinet.set(false);
    this.recherche.set('');
  }
}
