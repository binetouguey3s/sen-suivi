import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

// Lorsqu'on navigue vers une route protégée, on redirige vers la page de connexion si l'utilisateur n'est pas connecté
export const estConnecteGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.estConnecte() ? true : inject(Router).parseUrl('/connexion');
};
