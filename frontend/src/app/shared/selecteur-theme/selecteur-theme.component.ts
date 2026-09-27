import { ChangeDetectionStrategy, Component, ElementRef, booleanAttribute, inject, input, viewChildren } from '@angular/core';

import { NomIcone } from '../../core/icons/icons';
import { Theme, ThemeService } from '../../core/services/theme.service';
import { IconComponent } from '../icon/icon.component';

interface OptionTheme {
  valeur: Theme;
  libelle: string;
  description: string;
  icone: NomIcone;
}

const OPTIONS: OptionTheme[] = [
  { valeur: 'clair', libelle: 'Clair', description: 'Thème clair', icone: 'soleil' },
  { valeur: 'sombre', libelle: 'Sombre', description: 'Thème sombre', icone: 'lune' },
  { valeur: 'systeme', libelle: 'Système', description: "Thème de l'appareil", icone: 'ecran' },
];

// Choix du thème (ss-selecteur-theme) : groupe de boutons radio accessible.
// Un seul arrêt de tabulation, flèches pour changer d'option, comme un
// groupe de boutons radio natif. En version compacte, seules les icônes
// sont visibles ; le libellé reste lu par les lecteurs d'écran.
@Component({
  selector: 'ss-selecteur-theme',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './selecteur-theme.component.html',
  styleUrl: './selecteur-theme.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '[class.st--compact]': 'compact()' },
})
export class SelecteurThemeComponent {
  protected readonly theme = inject(ThemeService);
  protected readonly options = OPTIONS;

  readonly compact = input(false, { transform: booleanAttribute });

  private readonly boutons = viewChildren<ElementRef<HTMLButtonElement>>('bouton');

  protected choisir(valeur: Theme): void {
    this.theme.choisir(valeur);
  }

  protected clavier(evenement: KeyboardEvent, index: number): void {
    const dernier = this.options.length - 1;
    const cibles: Record<string, number> = {
      ArrowRight: index === dernier ? 0 : index + 1,
      ArrowDown: index === dernier ? 0 : index + 1,
      ArrowLeft: index === 0 ? dernier : index - 1,
      ArrowUp: index === 0 ? dernier : index - 1,
      Home: 0,
      End: dernier,
    };
    const cible = cibles[evenement.key];
    if (cible === undefined) return;
    evenement.preventDefault();
    // Comme pour un bouton radio natif, déplacer le focus sélectionne l'option
    this.choisir(this.options[cible].valeur);
    this.boutons()[cible]?.nativeElement.focus();
  }
}
