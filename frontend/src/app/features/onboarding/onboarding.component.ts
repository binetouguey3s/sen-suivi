import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { IconComponent } from '../../shared/icon/icon.component';

const ETAPES = [
  {
    titre: 'Notez votre humeur en dix secondes',
    texte: 'Un suivi quotidien qui permet de voir évoluer son ressenti dans la durée.',
    image: '/images/illustrations/onboarding-1-humeur.svg',
  },
  {
    titre: "Un chatbot à l'écoute, sans jugement",
    texte: "L'échange est confidentiel. Le chatbot ne remplace jamais un professionnel de santé.",
    image: '/images/illustrations/onboarding-2-chatbot.svg',
  },
  {
    titre: 'Des professionnels près de chez vous, à Dakar comme en région',
    texte: 'Accédez à un réseau de psychologues, sophrologues et coachs validés pour un accompagnement sur mesure.',
    image: '/images/illustrations/onboarding-3-professionnels.svg',
  },
];

@Component({
  selector: 'ss-onboarding',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './onboarding.component.html',
  styleUrl: './onboarding.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingComponent {
  private readonly router = inject(Router);

  protected readonly etapes = ETAPES;
  protected readonly index = signal(0);
  protected readonly etape = computed(() => ETAPES[this.index()]);
  protected readonly derniere = computed(() => this.index() === ETAPES.length - 1);

  protected async suivant(): Promise<void> {
    if (this.derniere()) {
      await this.terminer();
    } else {
      this.index.update((i) => i + 1);
    }
  }

  protected async terminer(): Promise<void> {
    await this.router.navigateByUrl('/app');
  }
}
