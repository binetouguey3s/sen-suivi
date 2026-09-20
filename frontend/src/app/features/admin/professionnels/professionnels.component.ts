import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { ProfessionnelAdmin, StatutValidationPro } from '../../../core/models/administration';
import { AdministrationService } from '../../../core/services/administration.service';
import { valeurs } from '../../../core/utils/ressource';
import { IconComponent } from '../../../shared/icon/icon.component';

type Onglet = 'TOUS' | StatutValidationPro;

@Component({
  selector: 'ss-admin-professionnels',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './professionnels.component.html',
  styleUrl: './professionnels.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminProfessionnelsComponent {
  private readonly administration = inject(AdministrationService);

  protected readonly onglet = signal<Onglet>('TOUS');
  protected readonly recherche = signal('');
  protected readonly selection = signal<Set<number>>(new Set());
  protected readonly enCours = signal<number | null>(null);
  protected readonly enCoursSelection = signal(false);
  protected readonly erreur = signal<string | null>(null);
  private minuteur: ReturnType<typeof setTimeout> | undefined;

  protected readonly onglets: { valeur: Onglet; libelle: string }[] = [
    { valeur: 'TOUS', libelle: 'Tous' },
    { valeur: 'EN_ATTENTE', libelle: 'En attente' },
    { valeur: 'VALIDE', libelle: 'Validé' },
    { valeur: 'REFUSE', libelle: 'Refusé' },
  ];

  protected readonly professionnels = httpResource<ProfessionnelAdmin[]>(
    () => {
      const params = new URLSearchParams();
      const o = this.onglet();
      const q = this.recherche().trim();
      if (o !== 'TOUS') params.set('statut', o);
      if (q) params.set('q', q);
      const chaine = params.toString();
      return `${API_BASE_URL}/professionnels${chaine ? `?${chaine}` : ''}`;
    },
    { defaultValue: [] },
  );
  protected readonly liste = computed(() => valeurs(this.professionnels));
  protected readonly nombreSelectionnes = computed(() => this.selection().size);

  protected dateInscription(iso: string): string {
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  protected saisirRecherche(evenement: Event): void {
    const valeur = (evenement.target as HTMLInputElement).value;
    clearTimeout(this.minuteur);
    this.minuteur = setTimeout(() => this.recherche.set(valeur), 250);
  }

  protected changerOnglet(o: Onglet): void {
    this.onglet.set(o);
    this.selection.set(new Set());
  }

  protected basculerSelection(id: number): void {
    const actuelle = new Set(this.selection());
    actuelle.has(id) ? actuelle.delete(id) : actuelle.add(id);
    this.selection.set(actuelle);
  }

  protected toutSelectionner(coche: boolean): void {
    this.selection.set(coche ? new Set(this.liste().filter((p) => p.statut_validation === 'EN_ATTENTE').map((p) => p.id)) : new Set());
  }

  protected async decider(professionnel: ProfessionnelAdmin, statut: StatutValidationPro): Promise<void> {
    this.enCours.set(professionnel.id);
    this.erreur.set(null);
    try {
      await this.administration.validerProfessionnel(professionnel.id, statut);
      this.professionnels.reload();
    } catch {
      this.erreur.set("L'action a échoué. Réessayez dans un instant.");
    } finally {
      this.enCours.set(null);
    }
  }

  protected async deciderSelection(statut: StatutValidationPro): Promise<void> {
    this.enCoursSelection.set(true);
    this.erreur.set(null);
    try {
      await Promise.all([...this.selection()].map((id) => this.administration.validerProfessionnel(id, statut)));
      this.selection.set(new Set());
      this.professionnels.reload();
    } catch {
      this.erreur.set("L'action a échoué pour au moins un profil. Réessayez dans un instant.");
    } finally {
      this.enCoursSelection.set(false);
    }
  }
}
