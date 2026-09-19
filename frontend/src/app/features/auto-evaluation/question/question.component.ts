import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { QuestionEvaluation, estTypeEvaluation } from '../../../core/models/evaluation';
import { AutoEvaluationService } from '../../../core/services/auto-evaluation.service';
import { CourbeMarqueComponent } from '../../../shared/courbe-marque/courbe-marque.component';
import { IconComponent } from '../../../shared/icon/icon.component';

@Component({
  selector: 'ss-evaluation-question',
  standalone: true,
  imports: [RouterLink, IconComponent, CourbeMarqueComponent],
  templateUrl: './question.component.html',
  styleUrl: './question.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuestionComponent {
  private readonly router = inject(Router);
  private readonly service = inject(AutoEvaluationService);

  // Paramètre de route :type (withComponentInputBinding)
  readonly type = input<string>();

  protected readonly typeValide = computed(() => {
    const t = this.type();
    return estTypeEvaluation(t) ? t : null;
  });

  protected readonly questions = httpResource<QuestionEvaluation[]>(
    () => {
      const type = this.typeValide();
      return type ? `${API_BASE_URL}/auto-evaluations/questions/${type}` : undefined;
    },
    { defaultValue: [] },
  );

  protected readonly index = signal(0);
  // Réponses choisies : identifiant de question -> identifiant d'option
  protected readonly reponses = signal<Record<number, number>>({});
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);

  protected readonly total = computed(() => this.questions.value().length);
  protected readonly courante = computed(() => this.questions.value()[this.index()] ?? null);
  protected readonly optionChoisie = computed(() => {
    const q = this.courante();
    return q ? (this.reponses()[q.id] ?? null) : null;
  });
  protected readonly estDerniere = computed(() => this.index() === this.total() - 1);
  protected readonly progression = computed(() =>
    this.total() ? ((this.index() + 1) / this.total()) * 100 : 0,
  );

  protected choisir(optionId: number): void {
    const q = this.courante();
    if (!q) return;
    this.reponses.update((r) => ({ ...r, [q.id]: optionId }));
  }

  protected precedent(): void {
    this.erreur.set(null);
    this.index.update((i) => Math.max(0, i - 1));
  }

  protected async suivant(): Promise<void> {
    if (this.optionChoisie() === null) return;
    if (!this.estDerniere()) {
      this.index.update((i) => i + 1);
      return;
    }

    const type = this.typeValide();
    if (!type) return;
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    try {
      const reponses = Object.entries(this.reponses()).map(([question, option]) => ({
        question: Number(question),
        option,
      }));
      await this.service.soumettre(type, reponses);
      await this.router.navigate(['/app/evaluation', type, 'resultat']);
    } catch {
      this.erreur.set("L'envoi de vos réponses a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
  }
}
