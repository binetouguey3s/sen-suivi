import { NgComponentOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, Type, computed, input } from '@angular/core';

import { ICONES, NomIcone } from '../../core/icons/icons';

// 4 tailles, couleur héritée du texte environnant.
const TAILLES_PIXELS = { sm: 16, md: 20, lg: 24, xl: 32 } as const;
export type TailleIcone = keyof typeof TAILLES_PIXELS;

@Component({
  selector: 'ss-icon',
  standalone: true,
  imports: [NgComponentOutlet],
  template: `<ng-container *ngComponentOutlet="composant(); inputs: entrees()" />`,
  styles: [
    `
      :host {
        display: inline-flex;
        color: inherit;
        line-height: 0;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IconComponent {
  readonly nom = input.required<NomIcone>();
  readonly taille = input<TailleIcone>('md');

  protected readonly composant = computed<Type<unknown>>(() => ICONES[this.nom()]);
  protected readonly entrees = computed(() => ({
    size: TAILLES_PIXELS[this.taille()],
    strokeWidth: 2,
  }));
}
