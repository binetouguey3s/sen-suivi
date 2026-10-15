import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';

import { IconComponent } from '../icon/icon.component';

// Mêmes règles que le backend (valider_fichier_audio) : vérifiées ici pour
// prévenir tout de suite, revérifiées côté serveur sur le contenu du fichier
export const EXTENSIONS_AUDIO = ['.mp3', '.m4a', '.ogg'];
export const AUDIO_MAX_OCTETS = 20 * 1024 * 1024;

export function erreurFichierAudio(fichier: File): string | null {
  const extension = fichier.name.slice(fichier.name.lastIndexOf('.')).toLowerCase();
  if (!EXTENSIONS_AUDIO.includes(extension)) return 'Formats acceptés : MP3, M4A ou OGG.';
  if (fichier.size > AUDIO_MAX_OCTETS) return 'Le fichier dépasse 20 Mo.';
  return null;
}

function taille(octets: number): string {
  return octets >= 1024 * 1024 ? `${(octets / (1024 * 1024)).toFixed(1).replace('.', ',')} Mo` : `${Math.ceil(octets / 1024)} Ko`;
}

// Champ « Fichier audio » d'un formulaire de ressource (ss-champ-audio) :
// choix du fichier, contrôle immédiat, progression de l'envoi, retrait.
// L'envoi lui-même revient au formulaire, qui connaît la ressource.
@Component({
  selector: 'ss-champ-audio',
  standalone: true,
  imports: [IconComponent],
  template: `
    <div class="ca">
      <p class="ca__libelle" id="ca-libelle">Fichier audio</p>

      @if (fichier(); as f) {
        <p class="ca__fichier"><ss-icon nom="ecouter" taille="sm" /> {{ f.name }} <span>({{ taille(f.size) }})</span></p>
      } @else if (actuel() && !retire()) {
        <div class="ca__actuel">
          <audio controls preload="none" [src]="actuel()" aria-label="Écouter le fichier actuel"></audio>
          <button type="button" class="ca__lien" [disabled]="desactive()" (click)="retirer()">Retirer le fichier</button>
        </div>
      } @else {
        <p class="ca__aide">Aucun fichier. Sans audio, la page proposera d’écouter le résumé avec la voix du navigateur.</p>
      }

      @if (progression() !== null) {
        <div class="ca__progression" role="progressbar" aria-labelledby="ca-libelle" aria-valuemin="0" aria-valuemax="100" [attr.aria-valuenow]="progression()">
          <span [style.width.%]="progression()"></span>
        </div>
        <p class="ca__aide" aria-live="polite">Envoi… {{ progression() }} %</p>
      }

      <label class="ca__choisir" [class.ca__choisir--desactive]="desactive()">
        <ss-icon nom="plus" taille="sm" /> {{ fichier() || actuel() ? 'Choisir un autre fichier' : 'Choisir un fichier audio' }}
        <input type="file" accept=".mp3,.m4a,.ogg,audio/mpeg,audio/mp4,audio/x-m4a,audio/ogg" [disabled]="desactive()" (change)="choisir($event)" />
      </label>
      <p class="ca__aide">MP3, M4A ou OGG, 20 Mo au plus. Vous devez détenir les droits de l’enregistrement.</p>
      @if (erreur()) {
        <p class="ca__erreur" role="alert">{{ erreur() }}</p>
      }
    </div>
  `,
  styleUrl: './champ-audio.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChampAudioComponent {
  // Adresse du fichier déjà enregistré (champ `audio` de l'API)
  readonly actuel = input<string | null | undefined>(null);
  // Pourcentage d'envoi en cours, ou null
  readonly progression = input<number | null>(null);
  readonly desactive = input(false);

  // Fichier choisi (null : choix annulé), ou demande de retrait du fichier actuel
  readonly fichierChange = output<File | null>();
  readonly retrait = output<void>();

  protected readonly fichier = signal<File | null>(null);
  protected readonly retire = signal(false);
  protected readonly erreur = signal<string | null>(null);
  protected readonly taille = taille;

  protected choisir(evenement: Event): void {
    const champ = evenement.target as HTMLInputElement;
    const fichier = champ.files?.[0] ?? null;
    const erreur = fichier ? erreurFichierAudio(fichier) : null;
    this.erreur.set(erreur);
    if (erreur) {
      champ.value = '';
      return;
    }
    this.fichier.set(fichier);
    this.retire.set(false);
    this.fichierChange.emit(fichier);
  }

  protected retirer(): void {
    this.retire.set(true);
    this.fichier.set(null);
    this.retrait.emit();
  }
}
