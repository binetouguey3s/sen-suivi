import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LecteurAudioComponent } from './lecteur-audio.component';

@Component({
  standalone: true,
  imports: [LecteurAudioComponent],
  template: `<ss-lecteur-audio [src]="src()" titre="La teranga commence par soi-même" resume="Un épisode pour souffler." cle="8" (dureeConnue)="duree = $event" />`,
})
class HoteComponent {
  readonly src = signal<string | null>('/audio/podcasts/teranga.mp3');
  duree = 0;
}

describe('LecteurAudioComponent', () => {
  let fixture: ComponentFixture<HoteComponent>;
  let hote: HTMLElement;
  let play: ReturnType<typeof vi.spyOn>;

  const audio = (): HTMLAudioElement => hote.querySelector('audio')!;
  const bouton = (texte: string | RegExp): HTMLButtonElement =>
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) =>
      typeof texte === 'string' ? b.textContent!.includes(texte) || b.getAttribute('aria-label') === texte : texte.test(b.textContent!),
    )!;

  // jsdom ne lit pas l'audio : la durée et la position sont simulées
  function metadonnees(duree: number): void {
    Object.defineProperty(audio(), 'duration', { value: duree, configurable: true });
    audio().dispatchEvent(new Event('loadedmetadata'));
    fixture.detectChanges();
  }

  async function creer(): Promise<void> {
    fixture = TestBed.createComponent(HoteComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
    await fixture.whenStable();
  }

  beforeEach(async () => {
    localStorage.clear();
    play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockImplementation(function (this: HTMLMediaElement) {
      Object.defineProperty(this, 'paused', { value: false, configurable: true });
      this.dispatchEvent(new Event('play'));
      return Promise.resolve();
    });
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(function (this: HTMLMediaElement) {
      Object.defineProperty(this, 'paused', { value: true, configurable: true });
      this.dispatchEvent(new Event('pause'));
    });
    vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => undefined);
    await TestBed.configureTestingModule({ imports: [HoteComponent] }).compileComponents();
    await creer();
  });

  afterEach(() => vi.restoreAllMocks());

  it('« Écouter le podcast » lance la lecture et devient « Mettre en pause »', async () => {
    Object.defineProperty(audio(), 'readyState', { value: 4, configurable: true });
    bouton('Écouter le podcast').click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(play).toHaveBeenCalledTimes(1);
    expect(hote.querySelector('.la__lecture')!.getAttribute('aria-label')).toBe('Mettre en pause');
  });

  it('lit la durée dans les métadonnées et la transmet à la page', () => {
    metadonnees(252);
    expect(hote.querySelector('.la__temps')!.textContent).toContain('04:12');
    expect(fixture.componentInstance.duree).toBe(252);
  });

  it('−15 s et +15 s déplacent la lecture', () => {
    metadonnees(120);
    audio().currentTime = 30;
    bouton('Avancer de 15 secondes').click();
    expect(audio().currentTime).toBe(45);
    bouton('Reculer de 15 secondes').click();
    bouton('Reculer de 15 secondes').click();
    bouton('Reculer de 15 secondes').click();
    expect(audio().currentTime).toBe(0);
  });

  it('les flèches du curseur déplacent de 5 secondes', () => {
    metadonnees(120);
    audio().currentTime = 20;
    hote.querySelector('input[type="range"]')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    expect(audio().currentTime).toBe(25);
  });

  it('la vitesse alterne entre 1×, 1,25× et 1,5×', () => {
    const vitesse = () => hote.querySelector<HTMLButtonElement>('.la__bouton--vitesse')!;
    expect(vitesse().textContent!.trim()).toBe('1×');
    vitesse().click();
    fixture.detectChanges();
    expect(vitesse().textContent!.trim()).toBe('1,25×');
    expect(audio().playbackRate).toBe(1.25);
    vitesse().click();
    vitesse().click();
    fixture.detectChanges();
    expect(vitesse().textContent!.trim()).toBe('1×');
  });

  it('propose de reprendre là où la personne s’était arrêtée', async () => {
    localStorage.setItem('ss_podcast_position_8', '192');
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({ imports: [HoteComponent] }).compileComponents();
    await creer();
    metadonnees(600);

    expect(bouton('Reprendre à').textContent).toContain('Reprendre à 03:12');
    bouton('Reprendre à').click();
    expect(audio().currentTime).toBe(192);
    expect(play).toHaveBeenCalled();
  });

  it('un fichier introuvable affiche un message et « Réessayer »', () => {
    audio().dispatchEvent(new Event('error'));
    fixture.detectChanges();

    expect(hote.querySelector('[role="alert"]')!.textContent).toContain('L’audio n’a pas pu être chargé.');
    bouton('Réessayer').click();
    expect(HTMLMediaElement.prototype.load).toHaveBeenCalled();
  });

  it('la lecture s’arrête quand on quitte la page', () => {
    const element = audio();
    fixture.destroy();
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
    expect(element).toBeTruthy();
  });

  describe('sans fichier audio', () => {
    let speak: ReturnType<typeof vi.fn>;

    beforeEach(async () => {
      speak = vi.fn();
      vi.stubGlobal('speechSynthesis', { speak, cancel: vi.fn(), pause: vi.fn(), resume: vi.fn(), getVoices: () => [] });
      vi.stubGlobal(
        'SpeechSynthesisUtterance',
        class {
          lang = '';
          constructor(readonly text: string) {}
        },
      );
      TestBed.resetTestingModule();
      await TestBed.configureTestingModule({ imports: [HoteComponent] }).compileComponents();
      fixture = TestBed.createComponent(HoteComponent);
      fixture.componentInstance.src.set(null);
      hote = fixture.nativeElement;
      fixture.detectChanges();
    });

    afterEach(() => {
      fixture.destroy();
      vi.unstubAllGlobals();
    });

    it('« Écouter le résumé » lit le texte avec la voix française du navigateur', () => {
      expect(hote.querySelector('audio')).toBeNull();
      bouton('Écouter le résumé').click();
      fixture.detectChanges();

      expect(speak).toHaveBeenCalledTimes(1);
      const enonce = speak.mock.calls[0][0];
      expect(enonce.lang).toBe('fr-FR');
      expect(enonce.text).toContain('Un épisode pour souffler.');
      expect(bouton('Pause')).toBeTruthy();
      expect(bouton('Arrêter')).toBeTruthy();
    });
  });
});
