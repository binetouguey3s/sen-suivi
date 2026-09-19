import { ChangeDetectionStrategy, Component, input } from '@angular/core';

// Structure commune des écrans d'authentification (connexion, inscriptions,
// mot de passe oublié) : panneau d'illustration à gauche, carte à droite.
@Component({
  selector: 'ss-layout-auth',
  standalone: true,
  templateUrl: './layout-auth.component.html',
  styleUrl: './layout-auth.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LayoutAuthComponent {
  readonly citation = input("Votre espace de sérénité, en toute discrétion.");
  readonly large = input(false);
}
