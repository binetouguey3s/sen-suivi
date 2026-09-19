import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import { NIVEAUX_HUMEUR, NiveauHumeur } from '../../core/models/suivi';

@Component({
  selector: 'ss-mood-selector',
  standalone: true,
  templateUrl: './mood-selector.component.html',
  styleUrl: './mood-selector.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MoodSelectorComponent {
  readonly selection = input<NiveauHumeur | null>(null);
  readonly desactive = input(false);
  readonly choisi = output<NiveauHumeur>();

  protected readonly niveaux = NIVEAUX_HUMEUR;
}
