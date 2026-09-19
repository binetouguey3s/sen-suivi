import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService, ErreurFormulaire } from '../../../core/services/auth.service';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { LayoutAuthComponent } from '../../../shared/layout-auth/layout-auth.component';

@Component({
  selector: 'ss-mot-de-passe-oublie',
  standalone: true,
  imports: [RouterLink, ChampComponent, IconComponent, LayoutAuthComponent],
  templateUrl: './mot-de-passe-oublie.component.html',
  styleUrl: './mot-de-passe-oublie.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MotDePasseOublieComponent {
  private readonly auth = inject(AuthService);

  protected readonly email = signal('');
  protected readonly enCours = signal(false);
  protected readonly envoye = signal(false);
  protected readonly erreur = signal<string | null>(null);

  protected async envoyer(evenement?: Event): Promise<void> {
    evenement?.preventDefault();
    if (!/^\S+@\S+\.\S+$/.test(this.email())) {
      this.erreur.set('Indiquez une adresse e-mail valide.');
      return;
    }
    this.erreur.set(null);
    this.enCours.set(true);
    try {
      await this.auth.demanderReinitialisation(this.email().trim());
      this.envoye.set(true);
    } catch (e) {
      this.erreur.set(e instanceof ErreurFormulaire ? (Object.values(e.champs)[0] ?? null) : null);
    } finally {
      this.enCours.set(false);
    }
  }
}
