import { ChangeDetectionStrategy, Component, computed, input, model, signal } from '@angular/core';

import { NomIcone } from '../../core/icons/icons';
import { IconComponent } from '../icon/icon.component';

let compteur = 0;

// Champ de formulaire (ss-input) : libellé, saisie, message d'erreur, œil pour les mots de passe.
@Component({
  selector: 'ss-champ',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './champ.component.html',
  styleUrl: './champ.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChampComponent {
  readonly libelle = input.required<string>();
  readonly type = input<'text' | 'email' | 'password' | 'number' | 'textarea'>('text');
  readonly valeur = model('');
  readonly placeholder = input('');
  readonly erreur = input<string | null>(null);
  readonly autocomplete = input('off');
  readonly icone = input<NomIcone | null>(null);
  readonly maxlength = input<number | null>(null);
  readonly lignes = input(4);

  protected readonly id = `champ-${++compteur}`;
  protected readonly visible = signal(false);
  protected readonly typeEffectif = computed(() =>
    this.type() === 'password' && this.visible() ? 'text' : this.type(),
  );

  protected saisir(evenement: Event): void {
    this.valeur.set((evenement.target as HTMLInputElement | HTMLTextAreaElement).value);
  }
}
