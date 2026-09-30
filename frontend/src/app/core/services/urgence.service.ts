import { Injectable, computed, signal } from '@angular/core';

const CLE = 'sen-suivi.jeton-urgence';

function lire(): string | null {
  try {
    return sessionStorage.getItem(CLE);
  } catch {
    return null;
  }
}

// Jeton remis par le chatbot quand il détecte une détresse. Tant qu'il est là
// (le temps de la session), la mise en relation est gratuite et l'interface
// n'affiche ni compteur, ni écran de paiement, ni tarif. Rien d'autre n'est
// gardé : la détresse elle-même n'est enregistrée nulle part.
@Injectable({ providedIn: 'root' })
export class UrgenceService {
  readonly jeton = signal<string | null>(lire());
  readonly enDetresse = computed(() => this.jeton() !== null);

  memoriser(jeton: string): void {
    this.jeton.set(jeton);
    try {
      sessionStorage.setItem(CLE, jeton);
    } catch {
      // Stockage indisponible : le jeton reste valable pour cette page
    }
  }
}
