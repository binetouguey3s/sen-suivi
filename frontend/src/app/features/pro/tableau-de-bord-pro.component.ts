import { HttpClient, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../../core/config/api.config';
import { AuthService } from '../../core/services/auth.service';
import { IconComponent } from '../../shared/icon/icon.component';
import { valeurs } from '../../core/utils/ressource';

interface Demande {
  id: number;
  date: string;
  date_reponse: string | null;
  statut: 'EN_ATTENTE' | 'ACCEPTEE' | 'REFUSEE';
  message: string;
  pseudonyme: string;
  ville: string;
  nom: string | null;
  email: string | null;
}

type Onglet = 'EN_ATTENTE' | 'ACCEPTEE' | 'REFUSEE';

@Component({
  selector: 'ss-tableau-de-bord-pro',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './tableau-de-bord-pro.component.html',
  styleUrl: './tableau-de-bord-pro.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TableauDeBordProComponent {
  private readonly http = inject(HttpClient);
  protected readonly auth = inject(AuthService);

  protected readonly demandes = httpResource<Demande[]>(() => `${API_BASE_URL}/demandes-contact`, { defaultValue: [] });
  protected readonly onglet = signal<Onglet>('EN_ATTENTE');
  protected readonly erreur = signal<string | null>(null);
  protected readonly enCours = signal<number | null>(null);

  protected readonly onglets: { valeur: Onglet; libelle: string }[] = [
    { valeur: 'EN_ATTENTE', libelle: 'En attente' },
    { valeur: 'ACCEPTEE', libelle: 'Acceptées' },
    { valeur: 'REFUSEE', libelle: 'Déclinées' },
  ];

  protected readonly enAttente = computed(() => valeurs(this.demandes).filter((d) => d.statut === 'EN_ATTENTE'));
  protected readonly accepteesCeMois = computed(() => {
    const maintenant = new Date();
    return this.demandes
      .value()
      .filter((d) => d.statut === 'ACCEPTEE' && d.date_reponse)
      .filter((d) => {
        const r = new Date(d.date_reponse!);
        return r.getMonth() === maintenant.getMonth() && r.getFullYear() === maintenant.getFullYear();
      }).length;
  });
  protected readonly affichees = computed(() => valeurs(this.demandes).filter((d) => d.statut === this.onglet()));

  protected compte(valeur: Onglet): number {
    return valeurs(this.demandes).filter((d) => d.statut === valeur).length;
  }

  protected depuis(iso: string): string {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (minutes < 60) return `Il y a ${Math.max(minutes, 1)} min`;
    const heures = Math.round(minutes / 60);
    if (heures < 24) return `Il y a ${heures} heures`;
    const jours = Math.round(heures / 24);
    return jours === 1 ? 'Hier' : `Il y a ${jours} jours`;
  }

  protected async repondre(demande: Demande, statut: 'ACCEPTEE' | 'REFUSEE'): Promise<void> {
    this.enCours.set(demande.id);
    this.erreur.set(null);
    try {
      await firstValueFrom(this.http.patch(`${API_BASE_URL}/demandes-contact/${demande.id}`, { statut }));
      this.demandes.reload();
    } catch {
      this.erreur.set('La réponse n’a pas pu être enregistrée. Réessayez dans un instant.');
    } finally {
      this.enCours.set(null);
    }
  }
}
