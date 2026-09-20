import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { IconComponent } from '../../../shared/icon/icon.component';
import { LayoutAuthComponent } from '../../../shared/layout-auth/layout-auth.component';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'ss-connexion',
  standalone: true,
  imports: [RouterLink, IconComponent, LayoutAuthComponent],
  templateUrl: './connexion.component.html',
  styleUrl: './connexion.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnexionComponent {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly email = signal('');
  protected readonly motDePasse = signal('');
  protected readonly afficherMotDePasse = signal(false);
  protected readonly enCours = signal(false);
  protected readonly erreur = signal<string | null>(null);

  protected saisirEmail(evenement: Event): void {
    this.email.set((evenement.target as HTMLInputElement).value);
  }

  protected saisirMotDePasse(evenement: Event): void {
    this.motDePasse.set((evenement.target as HTMLInputElement).value);
  }

  protected async valider(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.erreur.set(null);
    this.enCours.set(true);
    try {
      await this.auth.connecter(this.email(), this.motDePasse());
      await this.router.navigateByUrl(this.auth.espaceAccueil());
    } catch (erreur) {
      this.erreur.set((erreur as Error).message);
    } finally {
      this.enCours.set(false);
    }
  }
}
