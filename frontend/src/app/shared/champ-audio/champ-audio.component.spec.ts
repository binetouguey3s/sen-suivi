import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { AUDIO_MAX_OCTETS, ChampAudioComponent, erreurFichierAudio } from './champ-audio.component';

@Component({
  standalone: true,
  imports: [ChampAudioComponent],
  template: `<ss-champ-audio [actuel]="actuel()" [progression]="progression()" (fichierChange)="choisi = $event" (retrait)="retire = true" />`,
})
class HoteComponent {
  readonly actuel = signal<string | null>(null);
  readonly progression = signal<number | null>(null);
  choisi: File | null = null;
  retire = false;
}

function fichier(nom: string, octets = 1024): File {
  const f = new File([new Uint8Array(8)], nom, { type: 'audio/mpeg' });
  Object.defineProperty(f, 'size', { value: octets });
  return f;
}

describe('ChampAudioComponent', () => {
  let fixture: ComponentFixture<HoteComponent>;
  let hote: HTMLElement;

  function choisir(f: File): void {
    const champ = hote.querySelector<HTMLInputElement>('input[type="file"]')!;
    Object.defineProperty(champ, 'files', { value: [f], configurable: true });
    champ.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HoteComponent] }).compileComponents();
    fixture = TestBed.createComponent(HoteComponent);
    hote = fixture.nativeElement;
    fixture.detectChanges();
  });

  it('accepte MP3, M4A et OGG jusqu’à 20 Mo', () => {
    expect(erreurFichierAudio(fichier('episode.mp3'))).toBeNull();
    expect(erreurFichierAudio(fichier('episode.M4A'))).toBeNull();
    expect(erreurFichierAudio(fichier('episode.ogg'))).toBeNull();
    expect(erreurFichierAudio(fichier('episode.wav'))).toContain('MP3, M4A ou OGG');
    expect(erreurFichierAudio(fichier('episode.mp3', AUDIO_MAX_OCTETS + 1))).toContain('20 Mo');
  });

  it('transmet le fichier choisi et affiche son nom', () => {
    choisir(fichier('teranga.mp3', 3 * 1024 * 1024));
    expect(fixture.componentInstance.choisi?.name).toBe('teranga.mp3');
    expect(hote.textContent).toContain('teranga.mp3');
    expect(hote.textContent).toContain('3,0 Mo');
  });

  it('refuse tout de suite un mauvais format, sans le transmettre', () => {
    choisir(fichier('photo.png'));
    expect(fixture.componentInstance.choisi).toBeNull();
    expect(hote.querySelector('[role="alert"]')!.textContent).toContain('MP3, M4A ou OGG');
  });

  it('montre le fichier actuel et permet de le retirer', () => {
    fixture.componentInstance.actuel.set('http://localhost:8000/media/audio/teranga.mp3');
    fixture.detectChanges();
    expect(hote.querySelector('audio')!.getAttribute('src')).toBe('http://localhost:8000/media/audio/teranga.mp3');

    [...hote.querySelectorAll('button')].find((b) => b.textContent!.includes('Retirer'))!.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.retire).toBe(true);
    expect(hote.querySelector('audio')).toBeNull();
  });

  it('affiche la progression de l’envoi', () => {
    fixture.componentInstance.progression.set(42);
    fixture.detectChanges();
    const barre = hote.querySelector('[role="progressbar"]')!;
    expect(barre.getAttribute('aria-valuenow')).toBe('42');
    expect(hote.textContent).toContain('42 %');
  });
});
