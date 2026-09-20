import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

// Réserve une route à un ou plusieurs types de compte ; sinon, retour à l'espace du compte connecté.
export function typeCompteGuard(...types: ('utilisateur' | 'professionnel' | 'administrateur')[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);
    if (!auth.estConnecte()) return router.parseUrl('/connexion');
    const type = auth.typeCompte();
    return type && types.includes(type) ? true : router.parseUrl(auth.espaceAccueil());
  };
}
