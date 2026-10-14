import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, ElementRef, computed, inject, signal, viewChild } from '@angular/core';

import { RouterLink } from '@angular/router';

import { MoodSelectorComponent } from '../../shared/mood-selector/mood-selector.component';
import { API_BASE_URL } from '../../core/config/api.config';
import { SuiviHumeurService } from '../../core/services/suivi-humeur.service';
import { INFLUENCES_HUMEUR, NIVEAUX_HUMEUR, NiveauHumeur, SuiviHumeur } from '../../core/models/suivi';
import { valeurs } from '../../core/utils/ressource';
import { NOTE_MAX, ajouterDebut, phrasesDuJour } from './phrases';

@Component({
  selector: 'ss-journal',
  standalone: true,
  imports: [RouterLink, MoodSelectorComponent],
  templateUrl: './journal.component.html',
  styleUrl: './journal.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JournalComponent {
  private readonly suiviHumeurService = inject(SuiviHumeurService);

  protected readonly suivi = httpResource<SuiviHumeur[]>(
    () => `${API_BASE_URL}/suivi-humeur?periode=30j`,
    { defaultValue: [] },
  );

  protected readonly aujourdHui = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  protected readonly influences = INFLUENCES_HUMEUR;

  protected readonly humeurChoisie = signal<NiveauHumeur | null>(null);
  protected readonly note = signal('');
  protected readonly noteMax = NOTE_MAX;
  // Trois débuts de phrase, les mêmes toute la journée
  protected readonly phrases = phrasesDuJour(new Date());
  private readonly champNote = viewChild<ElementRef<HTMLTextAreaElement>>('champNote');
  protected readonly etiquettesChoisies = signal<string[]>([]);
  protected readonly enregistrementEnCours = signal(false);
  protected readonly erreur = signal<string | null>(null);
  protected readonly confirmation = signal(false);

  protected readonly entreesRecentes = computed(() =>
    [...valeurs(this.suivi)].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 5),
  );

  // Le début de phrase s'ajoute à la note, et le curseur se place à la fin pour continuer
  protected commencer(phrase: string): void {
    this.note.update((note) => ajouterDebut(note, phrase));
    const champ = this.champNote()?.nativeElement;
    if (champ) {
      champ.value = this.note();
      champ.focus();
      champ.setSelectionRange(champ.value.length, champ.value.length);
    }
  }

  protected basculerEtiquette(etiquette: string): void {
    this.etiquettesChoisies.update((liste) =>
      liste.includes(etiquette) ? liste.filter((e) => e !== etiquette) : [...liste, etiquette],
    );
  }

  protected emojiDe(niveau: NiveauHumeur): string {
    return NIVEAUX_HUMEUR.find((n) => n.valeur === niveau)?.emoji ?? '';
  }

  protected formaterDate(iso: string): { jour: string; libelle: string } {
    const date = new Date(`${iso}T00:00:00`);
    return {
      jour: date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
      libelle: date.toLocaleDateString('fr-FR', { weekday: 'long' }),
    };
  }

  protected async enregistrer(): Promise<void> {
    const humeur = this.humeurChoisie();
    if (!humeur) return;

    this.enregistrementEnCours.set(true);
    this.erreur.set(null);
    this.confirmation.set(false);
    try {
      await this.suiviHumeurService.publier(humeur, {
        note: this.note(),
        etiquettes: this.etiquettesChoisies(),
      });
      this.suivi.reload();
      this.confirmation.set(true);
    } catch {
      this.erreur.set("L'enregistrement a échoué. Réessayez dans un instant.");
    } finally {
      this.enregistrementEnCours.set(false);
    }
  }
}
