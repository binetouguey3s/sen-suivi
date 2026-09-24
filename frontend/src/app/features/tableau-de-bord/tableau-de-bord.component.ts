import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { IconComponent } from '../../shared/icon/icon.component';
import { MoodChartComponent, PointHumeur } from '../../shared/mood-chart/mood-chart.component';
import { MoodSelectorComponent } from '../../shared/mood-selector/mood-selector.component';
import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_LIEU } from '../../core/config/images-lieux';
import { AuthService } from '../../core/services/auth.service';
import { SuiviHumeurService } from '../../core/services/suivi-humeur.service';
import { valeurs } from '../../core/utils/ressource';
import {
  LieuDetente,
  NIVEAUX_HUMEUR,
  NiveauHumeur,
  Ressource,
  SuiviHumeur,
} from '../../core/models/suivi';

const JOURS_SEMAINE = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];

function formatDateISO(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function scoreDe(niveau: NiveauHumeur): number {
  return NIVEAUX_HUMEUR.find((n) => n.valeur === niveau)!.score;
}

@Component({
  selector: 'ss-tableau-de-bord',
  standalone: true,
  imports: [RouterLink, IconComponent, MoodSelectorComponent, MoodChartComponent],
  templateUrl: './tableau-de-bord.component.html',
  styleUrl: './tableau-de-bord.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TableauDeBordComponent {
  protected readonly auth = inject(AuthService);
  private readonly suiviHumeurService = inject(SuiviHumeurService);

  protected readonly suivi = httpResource<SuiviHumeur[]>(
    () => `${API_BASE_URL}/suivi-humeur?periode=30j`,
    { defaultValue: [] },
  );
  protected readonly ressources = httpResource<Ressource[]>(() => `${API_BASE_URL}/ressources`, {
    defaultValue: [],
  });
  protected readonly lieux = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, {
    defaultValue: [],
  });

  protected readonly enregistrementEnCours = signal(false);
  protected readonly erreurEnregistrement = signal<string | null>(null);

  protected readonly aujourdHui = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  protected readonly humeurDuJour = computed<NiveauHumeur | null>(() => {
    const auj = formatDateISO(new Date());
    return valeurs(this.suivi).find((e) => e.date === auj)?.score_humeur ?? null;
  });

  protected readonly pointsGraphique = computed<PointHumeur[]>(() => {
    const entrees = valeurs(this.suivi);
    const parDate = new Map(entrees.map((e) => [e.date, e.score_humeur]));
    const points: PointHumeur[] = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const iso = formatDateISO(date);
      const humeur = parDate.get(iso);
      points.push({
        libelle: JOURS_SEMAINE[date.getDay()],
        score: humeur ? scoreDe(humeur) : null,
      });
    }
    return points;
  });

  protected readonly moyenne = computed<number | null>(() => {
    const scores = this.pointsGraphique()
      .map((p) => p.score)
      .filter((s): s is number => s !== null);
    if (!scores.length) return null;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  });

  // La série en cours : jours consécutifs avec une entrée, remise à zéro après
  // un jour manqué. Si rien n'est encore
  // saisi aujourd'hui, on part d'hier pour ne pas casser une série existante.
  protected readonly serie = computed<number>(() => {
    const dates = new Set(valeurs(this.suivi).map((e) => e.date));
    const curseur = new Date();
    if (!dates.has(formatDateISO(curseur))) {
      curseur.setDate(curseur.getDate() - 1);
    }
    let jours = 0;
    while (dates.has(formatDateISO(curseur))) {
      jours++;
      curseur.setDate(curseur.getDate() - 1);
    }
    return jours;
  });

  protected readonly ressourceDuJour = computed<Ressource | null>(
    () => valeurs(this.ressources)[0] ?? null,
  );

  // Priorité à un lieu dont on a une vraie photo (docs/CREDITS-IMAGES.md) ;
  // à défaut, le premier lieu renvoyé par l'API.
  protected readonly lieuProche = computed<LieuDetente | null>(() => {
    const tous = valeurs(this.lieux);
    return tous.find((l) => l.nom in IMAGE_PAR_LIEU) ?? tous[0] ?? null;
  });

  protected readonly imageLieuProche = computed<string | null>(() => {
    const lieu = this.lieuProche();
    return lieu ? (IMAGE_PAR_LIEU[lieu.nom] ?? null) : null;
  });

  protected async choisirHumeur(niveau: NiveauHumeur): Promise<void> {
    this.enregistrementEnCours.set(true);
    this.erreurEnregistrement.set(null);
    try {
      await this.suiviHumeurService.publier(niveau);
      this.suivi.reload();
    } catch {
      this.erreurEnregistrement.set("L'enregistrement a échoué. Réessayez dans un instant.");
    } finally {
      this.enregistrementEnCours.set(false);
    }
  }
}
