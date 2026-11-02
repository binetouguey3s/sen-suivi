import { ChangeDetectionStrategy, Component, ElementRef, computed, inject, signal, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { IMAGE_PAR_PROFESSIONNEL } from '../../../core/config/images-professionnels';
import { LIBELLE_TYPE_EVALUATION, ProfessionnelSuggere, TypeEvaluation } from '../../../core/models/evaluation';
import { AutoEvaluationService } from '../../../core/services/auto-evaluation.service';
import { GaugeComponent } from '../../../shared/gauge/gauge.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../../shared/modal-urgence/modal-urgence.component';
import { ConversationService } from '../../../core/services/conversation.service';

export type Niveau = 'faible' | 'modere' | 'eleve';

// Phrase courte sous le titre, selon le niveau
const RESUME_PAR_NIVEAU: Record<Niveau, string> = {
  faible: 'Votre équilibre semble préservé. Continuez à prendre soin de vous.',
  modere: "Quelques tensions se font sentir. Vous pouvez agir dès aujourd'hui.",
  eleve: "Vous traversez une période chargée. Vous n'êtes pas seul·e : de l'aide existe.",
};

// Exercices proposés dans « Faire une pause guidée », sur le bon thème
const THEMATIQUE_PAR_TYPE: Record<TypeEvaluation, string> = {
  STRESS: 'Stress',
  ANXIETE: 'Respiration',
  FATIGUE: 'Sommeil',
};

@Component({
  selector: 'ss-evaluation-resultat',
  standalone: true,
  imports: [RouterLink, GaugeComponent, IconComponent, ModalUrgenceComponent],
  templateUrl: './resultat.component.html',
  styleUrl: './resultat.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ResultatComponent {
  protected readonly conversation = inject(ConversationService);
  private readonly router = inject(Router);
  protected readonly resultat = inject(AutoEvaluationService).dernierResultat;

  protected readonly modaleUrgenceOuverte = signal(false);
  private readonly sectionPros = viewChild<ElementRef<HTMLElement>>('pros');

  protected readonly niveaux: { valeur: Niveau; libelle: string }[] = [
    { valeur: 'faible', libelle: 'Faible' },
    { valeur: 'modere', libelle: 'Modéré' },
    { valeur: 'eleve', libelle: 'Élevé' },
  ];

  // Le niveau vient de l'interprétation du serveur (« Niveau modéré »), pas d'un seuil recalculé ici
  protected readonly niveau = computed<Niveau>(() => {
    const texte = (this.resultat()?.interpretation ?? '')
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .toLowerCase();
    if (texte.includes('elev')) return 'eleve';
    if (texte.includes('modere')) return 'modere';
    return 'faible';
  });

  // « Niveau de stress modéré » = type de l'évaluation + niveau (faible / modéré / élevé)
  protected readonly titre = computed(() => {
    const r = this.resultat();
    if (!r) return '';
    const niveau = r.interpretation.replace(/^Niveau\s+/i, '');
    return `Niveau ${LIBELLE_TYPE_EVALUATION[r.type_evaluation]} ${niveau}`;
  });

  protected readonly typeLibelle = computed(() => {
    const r = this.resultat();
    return r ? LIBELLE_TYPE_EVALUATION[r.type_evaluation] : '';
  });

  protected readonly resume = computed(() => RESUME_PAR_NIVEAU[this.niveau()]);

  // Le résultat n'a pas de date côté API : c'est celui qui vient d'être calculé
  protected readonly date = new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });

  // Repère « Vous » sur l'échelle, gardé dans les bords pour rester lisible
  protected readonly position = computed(() => Math.min(97, Math.max(3, this.resultat()?.score_de_tendance ?? 0)));

  protected readonly exercices = computed(() => {
    const r = this.resultat();
    return { format: 'EXERCICE', thematique: r ? THEMATIQUE_PAR_TYPE[r.type_evaluation] : null };
  });

  // Faible : on ne propose pas de professionnels
  protected readonly afficherPros = computed(() => this.niveau() !== 'faible');
  protected readonly vedette = computed(() => this.resultat()?.professionnels_suggeres[0] ?? null);
  protected readonly autres = computed(() => this.resultat()?.professionnels_suggeres.slice(1) ?? []);

  constructor() {
    // Le résultat n'existe qu'en mémoire : après un rechargement, retour à l'accueil.
    if (!this.resultat()) {
      void this.router.navigateByUrl('/app');
    }
  }

  protected allerAuxPros(): void {
    const section = this.sectionPros()?.nativeElement;
    if (!section) {
      void this.router.navigateByUrl('/professionnels');
      return;
    }
    const reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    section.scrollIntoView({ behavior: reduit ? 'auto' : 'smooth', block: 'start' });
    section.focus({ preventScroll: true });
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

  protected langues(pro: ProfessionnelSuggere): string {
    return pro.langue
      .split(',')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((l) => l.charAt(0).toUpperCase() + l.slice(1))
      .join(', ');
  }

  protected tarif(pro: ProfessionnelSuggere): string {
    return `${Math.round(pro.tarif_indicatif).toLocaleString('fr-FR')} FCFA`;
  }
}
