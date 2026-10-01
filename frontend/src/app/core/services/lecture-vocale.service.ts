import { Injectable, inject, signal } from '@angular/core';

import { ChatbotService } from './chatbot.service';

// Lecture à voix haute des réponses de Titou. Voix du serveur si un
// fournisseur est configuré, sinon voix française du navigateur. En cas
// d'échec, rien ne bloque : la réponse reste affichée en texte.
@Injectable({ providedIn: 'root' })
export class LectureVocaleService {
  private readonly chatbot = inject(ChatbotService);

  // Identifiant du message en cours de lecture
  readonly enLecture = signal<number | null>(null);
  private audio: HTMLAudioElement | null = null;
  private url: string | null = null;

  async lire(id: number, texte: string, jetonVocal: string | null | undefined): Promise<void> {
    this.arreter();
    this.enLecture.set(id);
    try {
      const son = jetonVocal ? await this.chatbot.lireAVoixHaute(texte, jetonVocal) : null;
      if (this.enLecture() !== id) return;
      if (son) {
        this.url = URL.createObjectURL(son);
        this.audio = new Audio(this.url);
        this.audio.onended = () => this.arreter();
        await this.audio.play();
        return;
      }
    } catch {
      // Synthèse du serveur indisponible : voix du navigateur
    }
    if (this.enLecture() === id) this.lireAvecLeNavigateur(texte);
  }

  arreter(): void {
    this.audio?.pause();
    this.audio = null;
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = null;
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
    this.enLecture.set(null);
  }

  private lireAvecLeNavigateur(texte: string): void {
    if (typeof speechSynthesis === 'undefined') {
      this.enLecture.set(null);
      return;
    }
    const enonce = new SpeechSynthesisUtterance(texte);
    enonce.lang = 'fr-FR';
    // Une voix française, féminine si l'appareil en propose une
    const voix = speechSynthesis.getVoices().filter((v) => v.lang.startsWith('fr'));
    enonce.voice = voix.find((v) => /female|femme|amelie|audrey|julie|marie|denise|hortense/i.test(v.name)) ?? voix[0] ?? null;
    enonce.rate = 0.95;
    enonce.onend = () => this.enLecture.set(null);
    enonce.onerror = () => this.enLecture.set(null);
    speechSynthesis.speak(enonce);
  }
}
