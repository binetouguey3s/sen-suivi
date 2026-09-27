import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { FenetreChatComponent } from './shared/fenetre-chat/fenetre-chat.component';

@Component({
  selector: 'ss-root',
  standalone: true,
  imports: [RouterOutlet, FenetreChatComponent],
  // La fenêtre de chat vit hors des pages : elle reste ouverte d'une page à l'autre
  template: '<router-outlet /><ss-fenetre-chat />',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {}
