import { Injectable, computed, signal } from '@angular/core';

// Durée maximale d'un message vocal (le serveur refuse proprement au-delà)
export const DUREE_MAX_SECONDES = 60;

export type EtatEnregistrement = 'pret' | 'enregistrement' | 'envoi';

// Enregistrement au micro, entièrement dans le navigateur : l'audio n'est
// jamais stocké, il part directement vers le serveur puis disparaît.
@Injectable({ providedIn: 'root' })
export class EnregistreurVocalService {
  readonly etat = signal<EtatEnregistrement>('pret');
  readonly secondes = signal(0);
  readonly erreur = signal<string | null>(null);
  readonly minuteur = computed(() => {
    const s = this.secondes();
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  });

  private enregistreur: MediaRecorder | null = null;
  private flux: MediaStream | null = null;
  private morceaux: Blob[] = [];
  private debut = 0;
  private intervalle: ReturnType<typeof setInterval> | undefined;
  private resoudre: ((resultat: { audio: Blob; duree: number } | null) => void) | null = null;

  get disponible(): boolean {
    return typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined';
  }

  // Demande explicite d'autorisation du micro, puis enregistrement.
  // Se résout à l'arrêt (bouton, ou durée maximale atteinte) ; null si annulé.
  async enregistrer(): Promise<{ audio: Blob; duree: number } | null> {
    this.erreur.set(null);
    if (!this.disponible) {
      this.erreur.set("Votre navigateur ne permet pas l'enregistrement vocal. Vous pouvez écrire votre message.");
      return null;
    }
    try {
      this.flux = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      const refus = e instanceof DOMException && (e.name === 'NotAllowedError' || e.name === 'SecurityError');
      this.erreur.set(
        refus
          ? "L'accès au micro a été refusé. Pour parler à Titou, autorisez le micro dans les réglages du navigateur (icône à gauche de l'adresse). Vous pouvez aussi écrire."
          : "Aucun micro n'a été trouvé. Vous pouvez écrire votre message.",
      );
      return null;
    }
    const type = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'].find((t) =>
      MediaRecorder.isTypeSupported(t),
    );
    this.morceaux = [];
    this.enregistreur = new MediaRecorder(this.flux, type ? { mimeType: type } : undefined);
    this.enregistreur.ondataavailable = (e) => e.data.size && this.morceaux.push(e.data);
    this.enregistreur.onstop = () => this.terminer();
    this.debut = Date.now();
    this.secondes.set(0);
    this.etat.set('enregistrement');
    this.enregistreur.start();
    this.intervalle = setInterval(() => {
      this.secondes.set(Math.floor((Date.now() - this.debut) / 1000));
      if (this.secondes() >= DUREE_MAX_SECONDES) this.arreter();
    }, 250);
    return new Promise((resoudre) => (this.resoudre = resoudre));
  }

  arreter(): void {
    if (this.enregistreur?.state === 'recording') this.enregistreur.stop();
  }

  annuler(): void {
    this.morceaux = [];
    const resoudre = this.resoudre;
    this.resoudre = null;
    this.arreter();
    this.liberer();
    this.etat.set('pret');
    resoudre?.(null);
  }

  private terminer(): void {
    const duree = (Date.now() - this.debut) / 1000;
    const audio = new Blob(this.morceaux, { type: this.enregistreur?.mimeType || 'audio/webm' });
    this.morceaux = [];
    this.liberer();
    const resoudre = this.resoudre;
    this.resoudre = null;
    if (!resoudre) return;
    if (duree < 0.5 || !audio.size) {
      this.etat.set('pret');
      resoudre(null);
      return;
    }
    this.etat.set('envoi');
    resoudre({ audio, duree: Math.min(duree, DUREE_MAX_SECONDES) });
  }

  private liberer(): void {
    clearInterval(this.intervalle);
    // Le voyant du micro s'éteint aussitôt
    this.flux?.getTracks().forEach((piste) => piste.stop());
    this.flux = null;
    this.enregistreur = null;
  }
}
