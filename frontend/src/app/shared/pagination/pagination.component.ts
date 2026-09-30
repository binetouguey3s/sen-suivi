import { ChangeDetectionStrategy, Component, computed, input, model } from '@angular/core';

import { IconComponent } from '../icon/icon.component';

// Tranche d'une liste pour la page demandée (une page au-delà de la fin
// affiche la dernière : après un filtre ou une suppression, rien ne disparaît)
export function tranche<T>(liste: T[], page: number, parPage: number): T[] {
  const derniere = Math.max(1, Math.ceil(liste.length / parPage));
  const p = Math.min(Math.max(1, page), derniere);
  return liste.slice((p - 1) * parPage, p * parPage);
}

type Element = number | '…';

// Pagination accessible, masquée quand tout tient sur une page.
@Component({
  selector: 'ss-pagination',
  standalone: true,
  imports: [IconComponent],
  template: `
    @if (pages() > 1) {
      <nav class="pg" aria-label="Pagination">
        <button type="button" class="pg__fleche" [disabled]="pageCourante() === 1" (click)="aller(pageCourante() - 1)" aria-label="Page précédente">
          <ss-icon nom="chevron-gauche" taille="sm" />
        </button>
        @for (e of elements(); track $index) {
          @if (e === '…') {
            <span class="pg__ellipse" aria-hidden="true">…</span>
          } @else {
            <button
              type="button"
              class="pg__page"
              [class.pg__page--active]="e === pageCourante()"
              [attr.aria-current]="e === pageCourante() ? 'page' : null"
              [attr.aria-label]="'Page ' + e"
              (click)="aller(e)"
            >
              {{ e }}
            </button>
          }
        }
        <button type="button" class="pg__fleche" [disabled]="pageCourante() === pages()" (click)="aller(pageCourante() + 1)" aria-label="Page suivante">
          <ss-icon nom="chevron-droite" taille="sm" />
        </button>
      </nav>
    }
  `,
  styles: [
    `
      .pg {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-top: var(--ss-espace-4);
      }
      .pg__page,
      .pg__fleche {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        height: 40px;
        padding: 0 10px;
        border: 1px solid var(--ss-bordure);
        border-radius: var(--ss-rayon-pilule);
        background: var(--ss-surface);
        color: var(--ss-texte);
        font-family: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .pg__fleche:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .pg__page--active {
        border-color: var(--ss-primaire);
        background: var(--ss-primaire);
        color: var(--ss-primaire-texte);
        font-weight: var(--ss-poids-texte-fort);
      }
      .pg__ellipse {
        padding: 0 4px;
        color: var(--ss-texte-doux);
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaginationComponent {
  readonly total = input.required<number>();
  readonly parPage = input.required<number>();
  readonly page = model(1);

  protected readonly pages = computed(() => Math.max(1, Math.ceil(this.total() / this.parPage())));
  protected readonly pageCourante = computed(() => Math.min(Math.max(1, this.page()), this.pages()));

  // 1 … 4 5 6 … 12 : la première, la dernière, et les voisines de la page courante
  protected readonly elements = computed<Element[]>(() => {
    const n = this.pages();
    const p = this.pageCourante();
    const numeros = [...new Set([1, p - 1, p, p + 1, n])].filter((x) => x >= 1 && x <= n).sort((a, b) => a - b);
    return numeros.flatMap((x, i) => (i > 0 && x - numeros[i - 1] > 1 ? (['…', x] as Element[]) : [x]));
  });

  protected aller(page: number): void {
    this.page.set(page);
  }
}
