import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { inject, provideAppInitializer } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling } from '@angular/router';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { jwtInterceptor } from './app/core/interceptors/jwt.interceptor';
import { ThemeService } from './app/core/services/theme.service';

bootstrapApplication(AppComponent, {
  providers: [
    // anchorScrolling : les liens /#experts et /#comment-ca-marche défilent jusqu'à la section
    provideRouter(routes, withComponentInputBinding(), withInMemoryScrolling({ anchorScrolling: 'enabled' })),
    provideHttpClient(withInterceptors([jwtInterceptor])),
    // Requis par ngx-charts (graphiques du tableau de bord professionnel)
    provideAnimationsAsync(),
    // Démarre le service de thème dès le lancement, pour suivre le réglage
    // de l'appareil même sur les pages sans sélecteur
    provideAppInitializer(() => {
      inject(ThemeService);
    }),
  ],
}).catch((error) => console.error(error));
