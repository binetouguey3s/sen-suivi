import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';

import { VideoYoutubeComponent, idYoutube } from './video-youtube.component';

@Component({
  standalone: true,
  imports: [VideoYoutubeComponent],
  template: `<ss-video-youtube [videoId]="id()" titre="Se détendre en 10 minutes" />`,
})
class HoteComponent {
  readonly id = signal<string | null>('aXItOY0sLRY');
}

function creer(id: string | null) {
  TestBed.configureTestingModule({ imports: [HoteComponent] });
  const fixture = TestBed.createComponent(HoteComponent);
  fixture.componentInstance.id.set(id);
  fixture.detectChanges();
  return { fixture, hote: fixture.nativeElement as HTMLElement };
}

describe('idYoutube', () => {
  it('reconnaît les liens YouTube, refuse les autres', () => {
    for (const lien of [
      'https://www.youtube.com/watch?v=aXItOY0sLRY',
      'https://youtu.be/aXItOY0sLRY?t=4',
      'https://www.youtube.com/shorts/aXItOY0sLRY',
      'https://www.youtube.com/embed/aXItOY0sLRY',
      'youtube.com/watch?feature=share&v=aXItOY0sLRY',
    ]) {
      expect(idYoutube(lien)).toBe('aXItOY0sLRY');
    }
    for (const lien of ['https://vimeo.com/1234', 'https://youtu.be/court', 'https://exemple.sn/?v=aXItOY0sLRY', 'javascript:alert(1)']) {
      expect(idYoutube(lien)).toBeNull();
    }
  });
});

describe('VideoYoutubeComponent', () => {
  it('montre la miniature, et ne crée l’iframe qu’au clic', () => {
    const { fixture, hote } = creer('aXItOY0sLRY');
    expect(hote.querySelector('iframe')).toBeNull();
    expect(hote.querySelector('img')!.getAttribute('src')).toBe('https://i.ytimg.com/vi/aXItOY0sLRY/hqdefault.jpg');

    hote.querySelector<HTMLButtonElement>('button')!.click();
    fixture.detectChanges();

    const cadre = hote.querySelector('iframe')!;
    expect(cadre.getAttribute('src')).toBe('https://www.youtube-nocookie.com/embed/aXItOY0sLRY?rel=0&autoplay=1');
    expect(cadre.getAttribute('title')).toBe('Se détendre en 10 minutes');
    expect(cadre.getAttribute('referrerpolicy')).toBe('strict-origin-when-cross-origin');
  });

  it('un identifiant invalide n’intègre rien', () => {
    for (const id of ['court', 'aXItOY0sLRY"><script>', 'https://evil.sn/embed/x', null]) {
      TestBed.resetTestingModule();
      const { hote } = creer(id);
      expect(hote.querySelector('iframe, img, button')).toBeNull();
    }
  });
});
