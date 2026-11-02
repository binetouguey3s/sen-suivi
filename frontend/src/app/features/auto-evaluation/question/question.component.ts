import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { LIBELLE_TYPE_EVALUATION, QuestionEvaluation, TypeEvaluation, estTypeEvaluation } from '../../../core/models/evaluation';
import { AutoEvaluationService } from '../../../core/services/auto-evaluation.service';
import { IconComponent } from '../../../shared/icon/icon.component';
import { valeurs } from '../../../core/utils/ressource';

// Photo d'ambiance de l'écran d'accueil, la même que sur la carte du tableau de bord
const PHOTO_PAR_TYPE: Record<TypeEvaluation, string> = {
  STRESS: '/images/accueil/stress.webp',
  ANXIETE: '/images/accueil/anxiete.webp',
  FATIGUE: '/images/accueil/fatigue.webp',
};

const ACCROCHE_PAR_TYPE: Record<TypeEvaluation, string> = {
  STRESS: 'Faites le point sur les tensions de votre quotidien, à votre rythme.',
  ANXIETE: 'Faites le point sur vos inquiétudes du moment, à votre rythme.',
  FATIGUE: 'Faites le point sur votre énergie et votre sommeil, à votre rythme.',
};

// Environ 15 secondes par question : 8 questions ≈ 2 minutes
const SECONDES_PAR_QUESTION = 15;
// Laisse le temps de voir la réponse cochée avant de passer à la suivante
const DELAI_AVANCE_MS = 350;

@Component({
  selector: 'ss-evaluation-question',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './question.component.html',
  styleUrl: './question.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown)': 'clavier($event)' },
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

  protected readonly titre = computed(() => {
    const t = this.typeValide();
    return t ? `Test ${LIBELLE_TYPE_EVALUATION[t]}` : 'Auto-évaluation';
  });
  protected readonly photo = computed(() => {
    const t = this.typeValide();
    return t ? PHOTO_PAR_TYPE[t] : null;
  });
  protected readonly accroche = computed(() => {
    const t = this.typeValide();
    return t ? ACCROCHE_PAR_TYPE[t] : '';
  });

  protected readonly questions = httpResource<QuestionEvaluation[]>(
    () => {
      const type = this.typeValide();
      return type ? `${API_BASE_URL}/auto-evaluations/questions/${type}` : undefined;
    },
    { defaultValue: [] },
  );

  // Écran d'accueil avant la première question
  protected readonly commence = signal(false);
  protected readonly index = signal(0);
  // Réponses choisies : identifiant de question -> identifiant d'option
  protected readonly reponses = signal<Record<number, number>>({});
  protected readonly envoiEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);

  private minuteur: ReturnType<typeof setTimeout> | undefined;

  protected readonly liste = computed(() => valeurs(this.questions));
  protected readonly total = computed(() => this.liste().length);
  protected readonly courante = computed(() => this.liste()[this.index()] ?? null);
  protected readonly optionChoisie = computed(() => {
    const q = this.courante();
    return q ? (this.reponses()[q.id] ?? null) : null;
  });
  protected readonly estDerniere = computed(() => this.index() === this.total() - 1);
  protected readonly minutesRestantes = computed(() =>
    Math.max(1, Math.round(((this.total() - this.index()) * SECONDES_PAR_QUESTION) / 60)),
  );

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.minuteur));
  }

  protected repondue(q: QuestionEvaluation): boolean {
    return this.reponses()[q.id] !== undefined;
  }

  // Un segment est cliquable s'il mène à une question déjà répondue ou à la première sans réponse
  protected accessible(i: number): boolean {
    const liste = this.liste();
    return liste.slice(0, i).every((q) => this.repondue(q));
  }

  // Petites barres de 0 à 4 : « Jamais » n'en remplit aucune, « Presque tout le temps » les remplit toutes
  protected intensite(position: number, nombre: number): number {
    return nombre > 1 ? Math.round((position / (nombre - 1)) * 4) : 0;
  }

  protected commencer(): void {
    this.commence.set(true);
  }

  protected aller(i: number): void {
    if (!this.accessible(i)) return;
    clearTimeout(this.minuteur);
    this.erreur.set(null);
    this.index.set(i);
  }

  protected choisir(optionId: number): void {
    const q = this.courante();
    if (!q) return;
    this.reponses.update((r) => ({ ...r, [q.id]: optionId }));

    // Passage automatique à la suivante ; la dernière attend « Voir mon résultat »
    clearTimeout(this.minuteur);
    if (!this.estDerniere()) {
      const depart = this.index();
      this.minuteur = setTimeout(() => {
        if (this.index() === depart) this.index.set(depart + 1);
      }, DELAI_AVANCE_MS);
    }
  }

  protected precedent(): void {
    clearTimeout(this.minuteur);
    this.erreur.set(null);
    if (this.index() === 0) {
      this.commence.set(false);
      return;
    }
    this.index.update((i) => i - 1);
  }

  // Touches 1 à 5 : choisit la réponse correspondante
  protected clavier(evenement: KeyboardEvent): void {
    if (!this.commence() || evenement.ctrlKey || evenement.metaKey || evenement.altKey) return;
    const q = this.courante();
    const rang = Number(evenement.key);
    if (!q || !Number.isInteger(rang) || rang < 1 || rang > q.options.length) return;
    evenement.preventDefault();
    this.choisir(q.options[rang - 1].id);
  }

  protected async suivant(): Promise<void> {
    if (this.optionChoisie() === null) return;
    clearTimeout(this.minuteur);
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
