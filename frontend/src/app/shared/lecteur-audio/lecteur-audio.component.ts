import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  computed,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';

import { IconComponent } from '../icon/icon.component';

// Vitesses proposées, dans l'ordre du bouton qui alterne
const VITESSES = [1, 1.25, 1.5] as const;
const SAUT_BOUTONS = 15;
const SAUT_CLAVIER = 5;
// Une position n'est proposée à la reprise qu'au-delà de 5 s, et avant les 5 dernières
const MARGE_REPRISE = 5;
const PREFIXE_POSITION = 'ss_podcast_position_';

// Voix du navigateur, si l'appareil en a une (vérifiée à chaque usage)
function synthese(): SpeechSynthesis | null {
  return typeof speechSynthesis !== 'undefined' ? speechSynthesis : null;
}

// Une seule lecture à la fois dans toute l'application
let lecteurEnCours: HTMLAudioElement | null = null;

export function minutesSecondes(secondes: number): string {
  const total = Math.max(0, Math.floor(secondes || 0));
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
}

function lirePosition(cle: string): number | null {
  try {
    const valeur = Number(localStorage.getItem(PREFIXE_POSITION + cle));
    return Number.isFinite(valeur) && valeur > 0 ? valeur : null;
  } catch {
    return null; // stockage indisponible (navigation privée) : pas de reprise, rien ne casse
  }
}

function ecrirePosition(cle: string, secondes: number | null): void {
  try {
    if (secondes === null) localStorage.removeItem(PREFIXE_POSITION + cle);
    else localStorage.setItem(PREFIXE_POSITION + cle, String(Math.floor(secondes)));
  } catch {
    // stockage indisponible : la reprise est un confort
  }
}

// Lecteur d'un podcast (ss-lecteur-audio) : <audio> natif, commandes aux couleurs
// du thème, reprise là où la personne s'était arrêtée, commandes de l'écran
// verrouillé (Media Session). Sans fichier, ou si le fichier est introuvable :
// le résumé est lu avec la voix française du navigateur.
@Component({
  selector: 'ss-lecteur-audio',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './lecteur-audio.component.html',
  styleUrl: './lecteur-audio.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LecteurAudioComponent implements OnDestroy {
  readonly src = input<string | null | undefined>(null);
  readonly titre = input.required<string>();
  readonly image = input<string | null>(null);
  // Texte lu par le navigateur quand il n'y a pas d'audio
  readonly resume = input('');
  // Identifiant pour mémoriser la position d'écoute (l'id de la ressource)
  readonly cle = input<string | number>('');
  // Durée réelle, en secondes, dès que les métadonnées sont lues
  readonly dureeConnue = output<number>();

  private readonly audio = viewChild<ElementRef<HTMLAudioElement>>('audio');

  protected readonly enLecture = signal(false);
  protected readonly chargement = signal(false);
  protected readonly erreur = signal(false);
  protected readonly position = signal(0);
  protected readonly duree = signal(0);
  protected readonly vitesse = signal<number>(VITESSES[0]);
  protected readonly reprise = signal<number | null>(null);

  // Sans fichier : on passe directement au résumé lu par le navigateur
  protected readonly avecAudio = computed(() => !!this.src());
  protected readonly libelleVitesse = computed(() => `${String(this.vitesse()).replace('.', ',')}×`);
  protected readonly tempsEcoule = computed(() => minutesSecondes(this.position()));
  protected readonly tempsTotal = computed(() => minutesSecondes(this.duree()));
  protected readonly valeurTexte = computed(() => `${this.tempsEcoule()} sur ${this.tempsTotal()}`);
  // Partie écoutée, pour colorer la barre de progression
  protected readonly progression = computed(() => `${this.duree() ? (this.position() / this.duree()) * 100 : 0}%`);
  protected readonly minutesSecondes = minutesSecondes;
  protected readonly sautBoutons = SAUT_BOUTONS;

  // Résumé lu par le navigateur : arrêté, en lecture ou en pause
  protected readonly resumeEtat = signal<'arrete' | 'lecture' | 'pause'>('arrete');
  protected readonly synthesePossible = !!synthese();

  private derniereSauvegarde = 0;

  ngOnDestroy(): void {
    const audio = this.element();
    if (audio) {
      this.memoriser();
      audio.pause();
      if (lecteurEnCours === audio) lecteurEnCours = null;
    }
    this.arreterResume();
  }

  private element(): HTMLAudioElement | null {
    return this.audio()?.nativeElement ?? null;
  }

  // ─── Lecture ───────────────────────────────────────────────────────────

  protected async basculer(): Promise<void> {
    const audio = this.element();
    if (!audio) return;
    if (!audio.paused) {
      audio.pause();
      return;
    }
    // Une seule lecture à la fois : l'autre lecteur, ou le résumé lu, s'arrête
    if (lecteurEnCours && lecteurEnCours !== audio) lecteurEnCours.pause();
    this.arreterResume();
    lecteurEnCours = audio;
    this.reprise.set(null);
    try {
      this.chargement.set(audio.readyState < 2);
      await audio.play();
    } catch {
      this.chargement.set(false);
    }
  }

  protected reprendre(): void {
    const audio = this.element();
    const depart = this.reprise();
    if (!audio || depart === null) return;
    audio.currentTime = depart;
    void this.basculer();
  }

  protected sauter(secondes: number): void {
    const audio = this.element();
    if (!audio) return;
    const fin = Number.isFinite(audio.duration) ? audio.duration : Infinity;
    audio.currentTime = Math.min(fin, Math.max(0, audio.currentTime + secondes));
    this.position.set(audio.currentTime);
  }

  protected changerVitesse(): void {
    const suivante = VITESSES[(VITESSES.indexOf(this.vitesse() as (typeof VITESSES)[number]) + 1) % VITESSES.length];
    this.vitesse.set(suivante);
    const audio = this.element();
    if (audio) audio.playbackRate = suivante;
  }

  protected chercher(evenement: Event): void {
    const audio = this.element();
    if (!audio) return;
    audio.currentTime = Number((evenement.target as HTMLInputElement).value);
    this.position.set(audio.currentTime);
  }

  // Flèches : ±5 s (le pas natif d'un curseur serait d'une seconde)
  protected clavierCurseur(evenement: KeyboardEvent): void {
    const pas = { ArrowRight: SAUT_CLAVIER, ArrowUp: SAUT_CLAVIER, ArrowLeft: -SAUT_CLAVIER, ArrowDown: -SAUT_CLAVIER }[
      evenement.key
    ];
    if (pas === undefined) return;
    evenement.preventDefault();
    this.sauter(pas);
  }

  protected reessayer(): void {
    this.erreur.set(false);
    this.chargement.set(true);
    this.element()?.load();
  }

  // ─── Événements de l'élément <audio> ───────────────────────────────────

  protected surMetadonnees(): void {
    const audio = this.element();
    if (!audio) return;
    this.chargement.set(false);
    this.erreur.set(false);
    audio.playbackRate = this.vitesse();
    if (Number.isFinite(audio.duration)) {
      this.duree.set(audio.duration);
      this.dureeConnue.emit(audio.duration);
    }
    const memorisee = lirePosition(String(this.cle()));
    const reprisePossible = memorisee !== null && memorisee > MARGE_REPRISE && memorisee < audio.duration - MARGE_REPRISE;
    this.reprise.set(reprisePossible ? memorisee : null);
  }

  protected surProgression(): void {
    const audio = this.element();
    if (!audio) return;
    this.position.set(audio.currentTime);
    // Position mémorisée toutes les 5 secondes d'écoute
    if (Math.abs(audio.currentTime - this.derniereSauvegarde) >= 5) this.memoriser();
  }

  protected surLecture(): void {
    this.enLecture.set(true);
    this.chargement.set(false);
    this.declarerSessionMedia();
  }

  protected surPause(): void {
    this.enLecture.set(false);
    this.memoriser();
  }

  protected surFin(): void {
    this.enLecture.set(false);
    ecrirePosition(String(this.cle()), null);
  }

  protected surErreur(): void {
    this.enLecture.set(false);
    this.chargement.set(false);
    this.erreur.set(true);
  }

  private memoriser(): void {
    const audio = this.element();
    const cle = String(this.cle());
    if (!audio || !cle || !audio.currentTime) return;
    this.derniereSauvegarde = audio.currentTime;
    ecrirePosition(cle, audio.currentTime);
  }

  // Titre, « Sen Suivi » et image sur l'écran verrouillé, avec ses commandes
  private declarerSessionMedia(): void {
    if (typeof navigator === 'undefined' || !('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') return;
    const image = this.image();
    navigator.mediaSession.metadata = new MediaMetadata({
      title: this.titre(),
      artist: 'Sen Suivi',
      artwork: image ? [{ src: new URL(image, location.origin).href }] : [],
    });
    navigator.mediaSession.setActionHandler('play', () => void this.basculer());
    navigator.mediaSession.setActionHandler('pause', () => this.element()?.pause());
    navigator.mediaSession.setActionHandler('seekbackward', () => this.sauter(-SAUT_BOUTONS));
    navigator.mediaSession.setActionHandler('seekforward', () => this.sauter(SAUT_BOUTONS));
  }

  // ─── Repli : le résumé lu par la voix du navigateur ─────────────────────

  protected ecouterResume(): void {
    const voix = synthese();
    if (!voix) return;
    if (this.resumeEtat() === 'pause') {
      voix.resume();
      this.resumeEtat.set('lecture');
      return;
    }
    lecteurEnCours?.pause();
    voix.cancel();
    const enonce = new SpeechSynthesisUtterance(`${this.titre()}. ${this.resume()}`);
    enonce.lang = 'fr-FR';
    const francaises = voix.getVoices().filter((v) => v.lang.startsWith('fr'));
    enonce.voice =
      francaises.find((v) => /female|femme|amelie|audrey|julie|marie|denise|hortense/i.test(v.name)) ?? francaises[0] ?? null;
    enonce.rate = 0.95;
    enonce.onend = () => this.resumeEtat.set('arrete');
    enonce.onerror = () => this.resumeEtat.set('arrete');
    voix.speak(enonce);
    this.resumeEtat.set('lecture');
  }

  protected pauseResume(): void {
    synthese()?.pause();
    this.resumeEtat.set('pause');
  }

  protected arreterResume(): void {
    if (this.resumeEtat() === 'arrete') return;
    synthese()?.cancel();
    this.resumeEtat.set('arrete');
  }
}
