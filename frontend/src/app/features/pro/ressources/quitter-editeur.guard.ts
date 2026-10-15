import { CanDeactivateFn } from '@angular/router';

import { EditeurRessourceComponent } from './editeur-ressource.component';

// Quitter l'éditeur avec des modifications : la modale propose d'enregistrer le brouillon
export const quitterEditeur: CanDeactivateFn<EditeurRessourceComponent> = (editeur) => editeur.peutQuitter();
