import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { IMAGE_PAR_LIEU } from '../../core/config/images-lieux';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
import { LieuDetente } from '../../core/models/suivi';
import { IconComponent } from '../../shared/icon/icon.component';
import { MoodChartComponent, PointHumeur } from '../../shared/mood-chart/mood-chart.component';

interface ProfessionnelPublic {
  id: number;
  nom: string;
  specialite_affichee: string;
  ville: string;
  tarif_indicatif: number;
}

@Component({
  selector: 'ss-accueil',
  standalone: true,
  imports: [RouterLink, IconComponent, MoodChartComponent],
  templateUrl: './accueil.component.html',
  styleUrl: './accueil.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccueilComponent {
  // Aperçu illustratif de la courbe d'humeur (non lié à un compte)
  protected readonly apercu: PointHumeur[] = [
    { libelle: 'L', score: 2 },
    { libelle: 'M', score: 3 },
    { libelle: 'M', score: 3 },
    { libelle: 'J', score: 4 },
    { libelle: 'V', score: 3 },
    { libelle: 'S', score: 4 },
    { libelle: 'D', score: 5 },
  ];

  private readonly tousLesLieux = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, {
    defaultValue: [],
  });
  private readonly tousLesPros = httpResource<ProfessionnelPublic[]>(
    () => `${API_BASE_URL}/professionnels/valides`,
    { defaultValue: [] },
  );

  // Uniquement les lieux dont on dispose d'une vraie photo
  protected readonly lieux = computed(() =>
    this.tousLesLieux.value().filter((l) => l.nom in IMAGE_PAR_LIEU).slice(0, 4),
  );
  protected readonly professionnels = computed(() => this.tousLesPros.value().slice(0, 3));

  protected image(lieu: LieuDetente): string {
    return IMAGE_PAR_LIEU[lieu.nom];
  }

  protected portrait(pro: ProfessionnelPublic): string | null {
    return IMAGE_PAR_PROFESSIONNEL[pro.nom] ?? null;
  }

  protected initiales(pro: ProfessionnelPublic): string {
    return pro.nom.split(' ').slice(0, 2).map((m) => m[0]).join('').toUpperCase();
  }

  protected tarif(pro: ProfessionnelPublic): string {
    return `${Math.round(pro.tarif_indicatif).toLocaleString('fr-FR')} FCFA`;
  }
}
