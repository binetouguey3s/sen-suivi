import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { CanalAlerte, PersonneConfiance, PersonneConfianceService } from '../../core/services/personne-confiance.service';
import { IconComponent } from '../icon/icon.component';

// Aide immédiate, en un geste : appeler les numéros d'urgence, ou prévenir sa
// personne de confiance. L'appel et le SMS partent du téléphone de la
// personne : c'est elle qui agit, rien n'est envoyé à sa place.
@Component({
  selector: 'ss-aide-immediate',
  standalone: true,
  imports: [RouterLink, IconComponent],
  template: `
    <div class="ai">
      @if (avecNumeros()) {
        <div class="ai__appels">
          <a class="ai__appel ai__appel--principal" href="tel:800805805"><ss-icon nom="telephone" taille="sm" /> Appeler le 800 805 805 <small>écoute, gratuit</small></a>
          <a class="ai__appel" href="tel:1515"><ss-icon nom="telephone" taille="sm" /> SAMU 1515</a>
          <a class="ai__appel" href="tel:18"><ss-icon nom="telephone" taille="sm" /> Pompiers 18</a>
        </div>
      }

      @if (estUtilisateur()) {
        @if (personne(); as p) {
          <div class="ai__confiance">
            <p class="ai__titre"><ss-icon nom="coeur" taille="sm" /> Prévenir {{ p.prenom }}@if (p.lien) { <span>({{ p.lien }})</span> }</p>
            <div class="ai__appels">
              @if (p.telephone) {
                <a class="ai__appel" [href]="'tel:' + p.telephone" (click)="tracer('APPEL')"><ss-icon nom="telephone" taille="sm" /> Appeler</a>
                <a class="ai__appel" [href]="lienSms()" (click)="tracer('SMS')"><ss-icon nom="chat" taille="sm" /> Envoyer un SMS</a>
              }
              @if (p.alerte_email_disponible) {
                <button type="button" class="ai__appel" [disabled]="emailEnvoye()" (click)="envoyerEmail()">
                  <ss-icon nom="courriel" taille="sm" /> {{ emailEnvoye() ? 'E-mail envoyé' : 'Prévenir par e-mail' }}
                </button>
              }
            </div>
            <p class="ai__note">{{ p.prenom }} reçoit seulement une invitation à prendre de vos nouvelles, jamais le contenu de vos échanges.</p>
          </div>
        } @else if (charge()) {
          <a class="ai__lien" routerLink="/app/parametres" fragment="personne-confiance">Ajouter une personne de confiance à prévenir en cas de besoin</a>
        }
      }
    </div>
  `,
  styles: [
    `
      .ai {
        display: flex;
        flex-direction: column;
        gap: var(--ss-espace-2);
        margin-top: var(--ss-espace-2);
      }
      .ai__appels {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .ai__appel {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        border: 1px solid var(--ss-bordure);
        border-radius: var(--ss-rayon-pilule);
        background: var(--ss-surface);
        color: var(--ss-texte);
        font-family: inherit;
        font-size: 14px;
        font-weight: var(--ss-poids-texte-fort);
        text-decoration: none;
        cursor: pointer;

        small {
          font-weight: normal;
          color: var(--ss-texte-doux);
        }
        &:disabled {
          opacity: 0.6;
          cursor: default;
        }
      }
      .ai__appel--principal {
        border-color: var(--ss-primaire);
        background: var(--ss-primaire);
        color: var(--ss-primaire-texte);

        small {
          color: inherit;
          opacity: 0.85;
        }
      }
      .ai__confiance {
        padding: var(--ss-espace-2);
        border-radius: var(--ss-rayon-champ);
        background: var(--ss-surface-douce);
      }
      .ai__titre {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: 0 0 var(--ss-espace-1);
        font-weight: var(--ss-poids-texte-fort);

        span {
          font-weight: normal;
          color: var(--ss-texte-doux);
        }
      }
      .ai__note {
        margin: var(--ss-espace-1) 0 0;
        color: var(--ss-texte-doux);
        font-size: 12px;
      }
      .ai__lien {
        color: var(--ss-texte-marque);
        font-size: 14px;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AideImmediateComponent {
  private readonly auth = inject(AuthService);
  private readonly service = inject(PersonneConfianceService);

  // La fenêtre d'urgence a déjà sa propre liste de numéros
  readonly avecNumeros = input(true);

  protected readonly estUtilisateur = computed(() => this.auth.typeCompte() === 'utilisateur');
  protected readonly personne = signal<PersonneConfiance | null>(null);
  protected readonly charge = signal(false);
  protected readonly emailEnvoye = signal(false);

  protected readonly lienSms = computed(() => {
    const p = this.personne();
    return p ? `sms:${p.telephone}?body=${encodeURIComponent(p.message_sms ?? '')}` : '';
  });

  constructor() {
    if (this.estUtilisateur()) {
      this.service
        .charger()
        .then((p) => this.personne.set(p))
        .catch(() => this.personne.set(null))
        .finally(() => this.charge.set(true));
    }
  }

  // Appel et SMS partent du téléphone : on garde seulement la trace du geste
  protected tracer(canal: CanalAlerte): void {
    this.service.alerter(canal).catch(() => undefined);
  }

  protected async envoyerEmail(): Promise<void> {
    try {
      await this.service.alerter('EMAIL');
      this.emailEnvoye.set(true);
    } catch {
      this.emailEnvoye.set(false);
    }
  }
}
