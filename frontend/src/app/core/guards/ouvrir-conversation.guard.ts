import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { ConversationService } from '../services/conversation.service';

// /chatbot n'est plus une page : l'adresse ouvre la fenêtre de conversation.
// Depuis une page de l'application, on y reste ; sur un lien direct (premier
// chargement), la fenêtre s'ouvre par-dessus l'accueil.
export const ouvrirConversation: CanActivateFn = () => {
  inject(ConversationService).ouvrir();
  const router = inject(Router);
  return router.navigated ? false : router.parseUrl('/');
};
