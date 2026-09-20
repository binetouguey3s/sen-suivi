import { ChangeDetectionStrategy, Component, inject, model, signal } from '@angular/core';

import { NotificationsService } from '../../core/services/notifications.service';
import { IconComponent } from '../icon/icon.component';

// Cloche + panneau des notifications (popover sur desktop, feuille sur mobile).
@Component({
  selector: 'ss-cloche-notifications',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './panneau-notifications.component.html',
  styleUrl: './panneau-notifications.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ClocheNotificationsComponent {
  protected readonly service = inject(NotificationsService);
  protected readonly ouvert = model(false);
  protected readonly toutAfficher = signal(false);

  protected bascule(): void {
    this.ouvert.update((o) => !o);
    if (this.ouvert()) void this.service.charger();
  }

  protected depuis(iso: string): string {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (minutes < 1) return "À l'instant";
    if (minutes < 60) return `Il y a ${minutes} min`;
    const heures = Math.round(minutes / 60);
    if (heures < 24) return `Il y a ${heures} h`;
    const jours = Math.round(heures / 24);
    return jours === 1 ? 'Hier' : `Il y a ${jours} jours`;
  }
}
