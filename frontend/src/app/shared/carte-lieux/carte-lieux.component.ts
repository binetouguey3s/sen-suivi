import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  effect,
  input,
  output,
  viewChild,
} from '@angular/core';
import * as L from 'leaflet';

import { LieuDetente } from '../../core/models/suivi';
import { IconComponent } from '../icon/icon.component';

const PIN =
  '<svg viewBox="0 0 30 38" aria-hidden="true"><path d="M15 1C8 1 2.5 6.5 2.5 13.5 2.5 23 15 37 15 37S27.5 23 27.5 13.5C27.5 6.5 22 1 15 1Z"/><circle cx="15" cy="13.5" r="4.5" fill="white" stroke="none"/></svg>';

function icone(selection: boolean): L.DivIcon {
  return L.divIcon({
    className: selection ? 'ss-pin ss-pin--selection' : 'ss-pin',
    html: PIN,
    iconSize: [30, 38],
    iconAnchor: [15, 38],
  });
}

// Carte OpenStreetMap des lieux de détente (ss-map).
@Component({
  selector: 'ss-carte-lieux',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div #conteneur class="carte" role="application" aria-label="Carte des lieux de détente"></div>
    @if (!compact()) {
    <div class="carte__commandes">
      <button type="button" aria-label="Zoomer" (click)="zoom(1)"><ss-icon nom="plus" /></button>
      <button type="button" aria-label="Dézoomer" (click)="zoom(-1)"><ss-icon nom="moins" /></button>
      <button type="button" aria-label="Recentrer la carte" (click)="recentrer()"><ss-icon nom="localiser" /></button>
    </div>
    <div class="carte__legende">
      <p>Légende</p>
      <span><i class="carte__point"></i> Lieux de détente</span>
      <span><i class="carte__point carte__point--selection"></i> Sélectionné</span>
    </div>
    }
  `,
  styleUrl: './carte-lieux.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CarteLieuxComponent implements OnDestroy {
  readonly lieux = input.required<LieuDetente[]>();
  readonly selection = input<number | null>(null);
  readonly compact = input(false);
  readonly choisi = output<number>();
  readonly ouvrir = output<number>();

  private readonly conteneur = viewChild.required<ElementRef<HTMLElement>>('conteneur');
  private carte?: L.Map;
  private calque = L.layerGroup();
  private observateur?: ResizeObserver;

  constructor() {
    afterNextRender(() => {
      this.carte = L.map(this.conteneur().nativeElement, {
        zoomControl: false,
        attributionControl: true,
      }).setView([14.6, -17.3], 9);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© contributeurs OpenStreetMap',
      }).addTo(this.carte);
      this.calque.addTo(this.carte);
      // La carte peut être créée alors qu'elle est masquée (mobile) : on la recalcule dès qu'elle change de taille.
      this.observateur = new ResizeObserver(() => {
        this.carte?.invalidateSize();
        this.dessiner();
      });
      this.observateur.observe(this.conteneur().nativeElement);
      this.dessiner();
    });

    effect(() => {
      this.lieux();
      this.selection();
      this.dessiner();
    });
  }

  ngOnDestroy(): void {
    this.observateur?.disconnect();
    this.carte?.remove();
  }

  protected zoom(delta: number): void {
    this.carte?.setZoom((this.carte.getZoom() ?? 9) + delta);
  }

  protected recentrer(): void {
    this.ajuster();
  }

  private avecCoordonnees(): LieuDetente[] {
    return this.lieux().filter((l) => l.latitude !== null && l.longitude !== null);
  }

  private ajuster(): void {
    if (!this.carte) return;
    const points = this.avecCoordonnees().map((l) => L.latLng(l.latitude!, l.longitude!));
    if (points.length) this.carte.fitBounds(L.latLngBounds(points), { padding: [60, 60], maxZoom: 11 });
  }

  private dessiner(): void {
    // Une carte sans dimensions (masquée) ne sait pas se centrer : on attend qu'elle soit visible.
    if (!this.carte || this.carte.getSize().x === 0 || this.carte.getSize().y === 0) return;
    this.calque.clearLayers();
    const choisie = this.selection();
    for (const lieu of this.avecCoordonnees()) {
      const estChoisi = lieu.id === choisie;
      const repere = L.marker([lieu.latitude!, lieu.longitude!], {
        icon: icone(estChoisi),
        title: lieu.nom,
        zIndexOffset: estChoisi ? 1000 : 0,
      });
      repere.on('click', () => (estChoisi ? this.ouvrir.emit(lieu.id) : this.choisi.emit(lieu.id)));
      if (estChoisi) {
        repere.bindTooltip(lieu.nom, { permanent: true, direction: 'top', offset: [0, -34], className: 'ss-etiquette' });
      }
      repere.addTo(this.calque);
    }
    const actuel = this.avecCoordonnees().find((l) => l.id === choisie);
    if (actuel) this.carte.flyTo([actuel.latitude!, actuel.longitude!], this.compact() ? 11 : Math.max(this.carte.getZoom(), 10), { duration: 0.6 });
    else this.ajuster();
  }
}
