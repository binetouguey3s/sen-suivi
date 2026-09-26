import { HttpClient, httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { API_BASE_URL } from '../../core/config/api.config';
import { AuthService } from '../../core/services/auth.service';
import { IconComponent } from '../../shared/icon/icon.component';
import { SparklineComponent } from '../../shared/sparkline/sparkline.component';
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

const JOURS_COURBE_ATTENTE = 14;
const POINTS_COURBE_STATUT = 12;

function finDeJour(date: Date): number {
  const fin = new Date(date);
  fin.setHours(23, 59, 59, 999);
  return fin.getTime();
}

@Component({
  selector: 'ss-tableau-de-bord-pro',
  standalone: true,
  imports: [IconComponent, SparklineComponent],
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
  private readonly acceptees = computed(() =>
    valeurs(this.demandes).filter((d) => d.statut === 'ACCEPTEE' && d.date_reponse),
  );
  protected readonly accepteesCeMois = computed(() => {
    const maintenant = new Date();
    return this.acceptees().filter((d) => {
      const r = new Date(d.date_reponse!);
      return r.getMonth() === maintenant.getMonth() && r.getFullYear() === maintenant.getFullYear();
    }).length;
  });
  protected readonly affichees = computed(() => valeurs(this.demandes).filter((d) => d.statut === this.onglet()));

  // Courbes calculées à partir des vraies demandes, jamais inventées.
  // Nombre de demandes en attente à la fin de chacun des 14 derniers jours.
  protected readonly courbeAttente = computed(() => {
    const demandes = valeurs(this.demandes);
    return Array.from({ length: JOURS_COURBE_ATTENTE }, (_, i) => {
      const jour = new Date();
      jour.setDate(jour.getDate() - (JOURS_COURBE_ATTENTE - 1 - i));
      const fin = finDeJour(jour);
      return demandes.filter((d) => {
        if (new Date(d.date).getTime() > fin) return false;
        return d.statut === 'EN_ATTENTE' || (d.date_reponse !== null && new Date(d.date_reponse).getTime() > fin);
      }).length;
    });
  });

  // Cumul des demandes acceptées, jour après jour, depuis le début du mois.
  protected readonly courbeAcceptees = computed(() => {
    const aujourdHui = new Date();
    const cumul = Array.from({ length: aujourdHui.getDate() }, (_, i) => {
      const fin = finDeJour(new Date(aujourdHui.getFullYear(), aujourdHui.getMonth(), i + 1));
      const debut = new Date(aujourdHui.getFullYear(), aujourdHui.getMonth(), 1).getTime();
      return this.acceptees().filter((d) => {
        const r = new Date(d.date_reponse!).getTime();
        return r >= debut && r <= fin;
      }).length;
    });
    // Une courbe a besoin d'au moins deux points (le 1er du mois)
    return cumul.length > 1 ? cumul : [0, ...cumul];
  });

  // Statut stable : ligne plate
  protected readonly courbeStatut = Array.from({ length: POINTS_COURBE_STATUT }, () => 1);

  protected depuis(iso: string): string {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (minutes < 60) return `Il y a ${Math.max(minutes, 1)} min`;
    const heures = Math.round(minutes / 60);
    if (heures < 24) return heures === 1 ? 'Il y a 1 heure' : `Il y a ${heures} heures`;
    const jours = Math.round(heures / 24);
    return jours === 1 ? 'Hier' : `${jours} jours`;
  }

  // Format court de la carte mobile : « Il y a 2h », « Hier »
  protected depuisCourt(iso: string): string {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (minutes < 60) return `Il y a ${Math.max(minutes, 1)} min`;
    const heures = Math.round(minutes / 60);
    if (heures < 24) return `Il y a ${heures}h`;
    const jours = Math.round(heures / 24);
    return jours === 1 ? 'Hier' : `${jours} jours`;
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
