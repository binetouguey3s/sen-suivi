import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';

const ESPACES_PRIVES = ['/app', '/pro'];

export const jwtInterceptor: HttpInterceptorFn = (requete, suite) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  // La connexion et le renouvellement n'ont pas besoin de jeton
  if (requete.url.endsWith('/auth/login') || requete.url.endsWith('/auth/refresh')) {
    return suite(requete);
  }

  const avecJeton = (r: HttpRequest<unknown>, jeton: string | null) =>
    jeton ? r.clone({ setHeaders: { Authorization: `Bearer ${jeton}` } }) : r;

  return from(auth.jetonAccesValide()).pipe(
    switchMap((jeton) => suite(avecJeton(requete, jeton))),
    catchError((erreur: HttpErrorResponse) => {
      if (erreur?.status !== 401 || !auth.estConnecte()) return throwError(() => erreur);

      // Jeton refusé (révoqué, altéré) : une seule nouvelle tentative avec un jeton renouvelé
      return from(auth.jetonAccesValide(true)).pipe(
        switchMap((jeton) => suite(avecJeton(requete, jeton))),
        catchError((erreur2) => {
          if (erreur2?.status === 401) {
            auth.deconnecter();
            // Une page publique reste consultable ; seuls les espaces privés renvoient à la connexion
            if (ESPACES_PRIVES.some((e) => router.url.startsWith(e))) {
              void router.navigateByUrl('/connexion');
            }
          }
          return throwError(() => erreur2);
        }),
      );
    }),
  );
};
