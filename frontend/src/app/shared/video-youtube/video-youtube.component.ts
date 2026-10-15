import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { IconComponent } from '../icon/icon.component';

// Identifiant d'une vidéo YouTube : 11 caractères, et rien d'autre
export const ID_YOUTUBE = /^[A-Za-z0-9_-]{11}$/;

// Même règle que le backend (extraire_id_youtube) : identifiant, ou null
export function idYoutube(lien: string): string | null {
  const trouve = lien
    .trim()
    .match(
      /^(?:https?:\/\/)?(?:(?:www\.|m\.)?youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/)|youtu\.be\/|(?:www\.)?youtube-nocookie\.com\/embed\/)([^?&#/]+)/,
    );
  return trouve && ID_YOUTUBE.test(trouve[1]) ? trouve[1] : null;
}

// Vidéo YouTube (ss-video-youtube), économe en données : la miniature et un
// bouton Lecture d'abord, l'iframe seulement au clic.
// Sécurité : on ne fait jamais confiance à un lien saisi. L'identifiant est
// revérifié, puis l'adresse youtube-nocookie est construite ici ; c'est cette
// seule adresse construite qui passe par bypassSecurityTrustResourceUrl.
@Component({
  selector: 'ss-video-youtube',
  standalone: true,
  imports: [IconComponent],
  template: `
    @if (idValide(); as id) {
      <div class="vy">
        @if (lancee()) {
          <iframe
            class="vy__cadre"
            [src]="adresse()"
            [title]="titre()"
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
            referrerpolicy="strict-origin-when-cross-origin"
          ></iframe>
        } @else {
          <button type="button" class="vy__miniature" [attr.aria-label]="'Lire la vidéo : ' + titre()" (click)="lancee.set(true)">
            <img [src]="'https://i.ytimg.com/vi/' + id + '/hqdefault.jpg'" alt="" loading="lazy" />
            <span class="vy__lecture" aria-hidden="true"><ss-icon nom="lecture" /></span>
            <small>La vidéo se charge au clic</small>
          </button>
        }
      </div>
    }
  `,
  styleUrl: './video-youtube.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VideoYoutubeComponent {
  private readonly sanitizer = inject(DomSanitizer);

  readonly videoId = input<string | null | undefined>(null);
  readonly titre = input('Vidéo');

  protected readonly lancee = signal(false);
  protected readonly idValide = computed(() => {
    const id = this.videoId();
    return id && ID_YOUTUBE.test(id) ? id : null;
  });
  protected readonly adresse = computed<SafeResourceUrl | null>(() => {
    const id = this.idValide();
    return id
      ? this.sanitizer.bypassSecurityTrustResourceUrl(`https://www.youtube-nocookie.com/embed/${id}?rel=0&autoplay=1`)
      : null;
  });
}
