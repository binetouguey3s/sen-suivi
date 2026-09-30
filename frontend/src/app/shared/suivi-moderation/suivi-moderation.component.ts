import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, input, output, signal } from '@angular/core';

import { ForumService, MonMessageForum, TypeMessageForum } from '../../core/services/forum.service';
import { IconComponent } from '../icon/icon.component';

// Suivi d'un message qu'on vient d'envoyer : relu en quelques secondes par la
// modération automatique, puis publié, accompagné, ou expliqué s'il ne l'est
// pas. Une décision automatique peut toujours être contestée.
const INTERVALLE_MS = 1500;
const ESSAIS_MAX = 10;

@Component({
  selector: 'ss-suivi-moderation',
  standalone: true,
  imports: [IconComponent],
  template: `
    @switch (etat()) {
      @case ('VERIFICATION') {
        <p class="sm sm--attente" role="status"><span class="sm__roue" aria-hidden="true"></span> Vérification de votre message…</p>
      }
      @case ('VISIBLE') {
        <div class="sm sm--ok" role="status">
          <p><ss-icon nom="verifie" taille="sm" /> Votre message est publié.</p>
          @if (message().message) { <p class="sm__soutien">{{ message().message }}</p> }
        </div>
      }
      @case ('BLOQUE') {
        <div class="sm sm--bloque" role="status">
          <p>{{ message().message || "Votre message n'a pas été publié." }}</p>
          <div class="sm__actions">
            <button type="button" class="sm__bouton" (click)="reformuler.emit(message().contenu)">Reformuler</button>
            @if (message().peut_contester && !contestation()) {
              <button type="button" class="sm__lien" (click)="contester()">Demander un réexamen</button>
            }
          </div>
          @if (contestation(); as c) { <p class="sm__note">{{ c }}</p> }
        </div>
      }
      @default {
        <div class="sm sm--attente" role="status">
          <p><ss-icon nom="horloge" taille="sm" /> {{ message().message || "Votre message est en cours de relecture par l'équipe de Sen Suivi. Il sera publié très vite s'il respecte la charte." }}</p>
        </div>
      }
    }
  `,
  styles: [
    `
      .sm {
        margin: 0;
        padding: var(--ss-espace-2) var(--ss-espace-3);
        border-radius: var(--ss-rayon-champ);
        background: var(--ss-surface-douce);
        color: var(--ss-texte);
        line-height: 1.5;

        p {
          display: flex;
          align-items: flex-start;
          gap: 6px;
          margin: 0;
        }
      }
      .sm--ok {
        background: var(--ss-surface-accent);
      }
      .sm--bloque {
        border: 1px solid var(--ss-bordure);
        background: var(--ss-surface);
      }
      .sm p.sm__soutien,
      .sm p.sm__note {
        margin-top: var(--ss-espace-1);
        font-size: 14px;
      }
      .sm__actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--ss-espace-2);
        margin-top: var(--ss-espace-2);
      }
      .sm__bouton {
        padding: 8px var(--ss-espace-2);
        border: none;
        border-radius: var(--ss-rayon-bouton);
        background: var(--ss-primaire);
        color: var(--ss-primaire-texte);
        font-family: inherit;
        cursor: pointer;
      }
      .sm__lien {
        padding: 0;
        border: none;
        background: none;
        color: var(--ss-texte-marque);
        font-family: inherit;
        text-decoration: underline;
        cursor: pointer;
      }
      .sm__roue {
        width: 14px;
        height: 14px;
        margin-top: 4px;
        border: 2px solid var(--ss-bordure);
        border-top-color: var(--ss-primaire);
        border-radius: 50%;
        animation: tourner 0.8s linear infinite;
      }
      @keyframes tourner {
        to {
          transform: rotate(360deg);
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .sm__roue {
          animation: none;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SuiviModerationComponent implements OnInit {
  private readonly forum = inject(ForumService);

  readonly type = input.required<TypeMessageForum>();
  readonly idMessage = input.required<number>();
  // Publié : le parent peut recharger la liste ; reformuler : il rouvre la saisie
  readonly publie = output<void>();
  readonly reformuler = output<string>();

  protected readonly etat = signal<'VERIFICATION' | MonMessageForum['statut_moderation']>('VERIFICATION');
  protected readonly message = signal<MonMessageForum>({} as MonMessageForum);
  protected readonly contestation = signal<string | null>(null);
  private minuterie: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.minuterie));
  }

  ngOnInit(): void {
    void this.suivre(0);
  }

  private async suivre(essai: number): Promise<void> {
    try {
      const { messages } = await this.forum.mesMessages();
      const m = messages.find((x) => x.type === this.type() && x.id === this.idMessage());
      if (m && m.statut_moderation !== 'EN_ATTENTE') {
        this.message.set(m);
        this.etat.set(m.statut_moderation);
        if (m.statut_moderation === 'VISIBLE') this.publie.emit();
        return;
      }
      if (m && m.message) this.message.set(m);
    } catch {
      // Réseau momentanément indisponible : on réessaie
    }
    if (essai + 1 >= ESSAIS_MAX) {
      this.etat.set('EN_ATTENTE');
      return;
    }
    this.minuterie = setTimeout(() => void this.suivre(essai + 1), INTERVALLE_MS);
  }

  protected async contester(): Promise<void> {
    try {
      this.contestation.set((await this.forum.contester(this.type(), this.idMessage(), '')).detail);
    } catch {
      this.contestation.set("La demande de réexamen n'a pas pu être envoyée. Réessayez dans un instant.");
    }
  }
}
