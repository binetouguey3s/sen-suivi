import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { IMAGE_PAR_PROFESSIONNEL } from '../../../core/config/images-professionnels';
import { LIBELLE_TYPE_EVALUATION, ProfessionnelSuggere } from '../../../core/models/evaluation';
import { AutoEvaluationService } from '../../../core/services/auto-evaluation.service';
import { CourbeMarqueComponent } from '../../../shared/courbe-marque/courbe-marque.component';
import { GaugeComponent } from '../../../shared/gauge/gauge.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../../shared/modal-urgence/modal-urgence.component';

@Component({
  selector: 'ss-evaluation-resultat',
  standalone: true,
  imports: [RouterLink, GaugeComponent, IconComponent, ModalUrgenceComponent, CourbeMarqueComponent],
  templateUrl: './resultat.component.html',
  styleUrl: './resultat.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ResultatComponent {
  private readonly router = inject(Router);
  protected readonly resultat = inject(AutoEvaluationService).dernierResultat;

  protected readonly modaleUrgenceOuverte = signal(false);

  // « Niveau de stress modéré » = type de l'évaluation + niveau (faible / modéré / élevé)
  protected readonly titre = computed(() => {
    const r = this.resultat();
    if (!r) return '';
    const niveau = r.interpretation.replace(/^Niveau\s+/i, '');
    return `Niveau ${LIBELLE_TYPE_EVALUATION[r.type_evaluation]} ${niveau}`;
  });

  protected readonly niveauFaible = computed(() => (this.resultat()?.score_de_tendance ?? 0) <= 33);

  constructor() {
    // Le résultat n'existe qu'en mémoire : après un rechargement, retour à l'accueil.
    if (!this.resultat()) {
      void this.router.navigateByUrl('/app');
    }
  }

  protected portrait(pro: ProfessionnelSuggere): string | null {
    return IMAGE_PAR_PROFESSIONNEL[pro.nom] ?? null;
  }

  protected initiales(pro: ProfessionnelSuggere): string {
    return pro.nom
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((m) => m[0])
      .join('')
      .toUpperCase();
  }

  protected langues(pro: ProfessionnelSuggere): string[] {
    return pro.langue
      .split(',')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => l.charAt(0).toUpperCase() + l.slice(1));
  }

  protected tarif(pro: ProfessionnelSuggere): string {
    return `${Math.round(pro.tarif_indicatif).toLocaleString('fr-FR')} FCFA`;
  }
}
