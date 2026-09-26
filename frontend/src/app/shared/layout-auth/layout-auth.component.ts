import { ChangeDetectionStrategy, Component, input } from '@angular/core';

// Structure commune des écrans d'authentification (connexion, inscriptions,
// mot de passe oublié) : photo en pleine hauteur à gauche, carte à droite.
@Component({
  selector: 'ss-layout-auth',
  standalone: true,
  templateUrl: './layout-auth.component.html',
  styleUrl: './layout-auth.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LayoutAuthComponent {
  readonly large = input(false);
  // Le logo s'efface sur les cartes qui portent déjà une grande icône (« Lien envoyé »)
  readonly logo = input(true);
  // Liens du pied de page, comme sur les maquettes : « legal » pour la connexion
  // et les inscriptions, « aide » pour la récupération du mot de passe
  readonly liensPied = input<'legal' | 'aide'>('legal');
  protected readonly annee = new Date().getFullYear();
}
