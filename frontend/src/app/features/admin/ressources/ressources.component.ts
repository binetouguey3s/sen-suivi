import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { API_BASE_URL } from '../../../core/config/api.config';
import { RessourceAdmin } from '../../../core/models/administration';
import { AdministrationService } from '../../../core/services/administration.service';
import { ICONE_PAR_TYPE, LIBELLE_PAR_TYPE } from '../../../core/utils/ressources';
import { valeurs } from '../../../core/utils/ressource';
import { STATUTS } from '../../pro/ressources/ressources-pro';
import { idYoutube } from '../../../shared/video-youtube/video-youtube.component';
import { ChampAudioComponent } from '../../../shared/champ-audio/champ-audio.component';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { PaginationComponent, tranche } from '../../../shared/pagination/pagination.component';

type Format = RessourceAdmin['type_ressource'];
const FORMATS: Format[] = ['ARTICLE', 'EXERCICE', 'PODCAST', 'VIDEO'];

@Component({
  selector: 'ss-admin-ressources',
  standalone: true,
  imports: [ChampComponent, ChampAudioComponent, IconComponent, ModalComponent, PaginationComponent],
  templateUrl: './ressources.component.html',
  styleUrl: './ressources.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminRessourcesComponent {
  private readonly administration = inject(AdministrationService);

  protected readonly formats = FORMATS.map((valeur) => ({
    valeur,
    libelle: LIBELLE_PAR_TYPE[valeur],
    icone: ICONE_PAR_TYPE[valeur],
  }));

  // Tous les statuts : les propositions des professionnels comprises
  protected readonly ressources = httpResource<RessourceAdmin[]>(() => `${API_BASE_URL}/ressources?statut=TOUS`, {
    defaultValue: [],
  });
  // Onglets : tout le catalogue, ou les propositions à relire
  protected readonly onglet = signal<'TOUTES' | 'A_VALIDER'>('TOUTES');
  protected readonly aValider = computed(() => valeurs(this.ressources).filter((r) => r.statut === 'EN_ATTENTE'));
  protected readonly liste = () => (this.onglet() === 'A_VALIDER' ? this.aValider() : valeurs(this.ressources));
  protected readonly libelleStatut = (r: RessourceAdmin) => STATUTS[r.statut ?? 'PUBLIEE'];

  // Pagination : 10 éléments par page
  protected readonly page = signal(1);
  protected readonly listePage = computed(() => tranche(this.liste(), this.page(), 20));

  protected readonly modaleOuverte = signal(false);
  protected readonly enEdition = signal<RessourceAdmin | null>(null);
  protected readonly titre = signal('');
  protected readonly formatChoisi = signal<Format>('ARTICLE');
  protected readonly thematique = signal('');
  protected readonly dureeLecture = signal(5);
  protected readonly contenu = signal('');
  protected readonly lienVideo = signal('');
  protected readonly envoiEnCours = signal(false);
  // Podcast : fichier choisi, demande de retrait du fichier actuel, progression de l'envoi
  protected readonly fichierAudio = signal<File | null>(null);
  protected readonly retirerAudio = signal(false);
  protected readonly progressionAudio = signal<number | null>(null);
  protected readonly erreur = signal<string | null>(null);

  protected readonly aSupprimer = signal<RessourceAdmin | null>(null);
  protected readonly suppressionOuverte = signal(false);
  protected readonly suppressionEnCours = signal(false);

  protected demanderSuppression(ressource: RessourceAdmin): void {
    this.aSupprimer.set(ressource);
    this.suppressionOuverte.set(true);
  }

  protected ouvrirCreation(): void {
    this.enEdition.set(null);
    this.titre.set('');
    this.formatChoisi.set('ARTICLE');
    this.thematique.set('');
    this.dureeLecture.set(5);
    this.contenu.set('');
    this.lienVideo.set('');
    this.reinitialiserAudio();
    this.erreur.set(null);
    this.modaleOuverte.set(true);
  }

  private reinitialiserAudio(): void {
    this.fichierAudio.set(null);
    this.retirerAudio.set(false);
    this.progressionAudio.set(null);
  }

  protected ouvrirEdition(ressource: RessourceAdmin): void {
    this.enEdition.set(ressource);
    this.titre.set(ressource.titre);
    this.formatChoisi.set(ressource.type_ressource);
    this.thematique.set(ressource.thematique);
    this.dureeLecture.set(ressource.duree_lecture);
    this.contenu.set(ressource.contenu);
    this.lienVideo.set(ressource.url_video ?? '');
    this.reinitialiserAudio();
    this.erreur.set(null);
    this.modaleOuverte.set(true);
  }

  protected iconeType(type: Format) {
    return ICONE_PAR_TYPE[type];
  }

  protected libelleType(type: Format): string {
    return LIBELLE_PAR_TYPE[type];
  }

  protected saisirDuree(evenement: Event): void {
    this.dureeLecture.set(Number((evenement.target as HTMLInputElement).value) || 0);
  }

  protected async enregistrer(): Promise<void> {
    if (!this.titre().trim() || !this.thematique().trim() || !this.contenu().trim()) {
      this.erreur.set('Merci de compléter le titre, la thématique et le contenu.');
      return;
    }
    if (this.formatChoisi() === 'VIDEO' && !idYoutube(this.lienVideo())) {
      this.erreur.set('Seuls les liens YouTube sont acceptés.');
      return;
    }
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    const donnees = {
      titre: this.titre().trim(),
      type_ressource: this.formatChoisi(),
      thematique: this.thematique().trim(),
      duree_lecture: this.dureeLecture(),
      contenu: this.contenu().trim(),
      url_video: this.formatChoisi() === 'VIDEO' ? this.lienVideo().trim() : '',
    };
    let id: number | null = null;
    try {
      const existante = this.enEdition();
      if (existante) {
        await this.administration.modifierRessource(existante.id, donnees);
        id = existante.id;
      } else {
        id = (await this.administration.creerRessource(donnees)).id;
      }
      // Puis le fichier audio d'un podcast, une fois la ressource enregistrée
      const fichier = this.fichierAudio();
      if (this.formatChoisi() === 'PODCAST' && fichier) {
        this.progressionAudio.set(0);
        await this.administration.envoyerAudio(id, fichier, (p) => this.progressionAudio.set(p));
      } else if (this.retirerAudio() && existante?.audio) {
        await this.administration.retirerAudio(id);
      }
      this.modaleOuverte.set(false);
      this.ressources.reload();
    } catch {
      this.erreur.set(
        id === null
          ? "L'enregistrement a échoué. Réessayez dans un instant."
          : "La ressource est enregistrée, mais le fichier audio n'a pas pu être envoyé. Vérifiez son format (MP3, M4A ou OGG, 20 Mo au plus) et réessayez.",
      );
      if (id !== null && !this.enEdition()) this.ressources.reload();
    } finally {
      this.envoiEnCours.set(false);
      this.progressionAudio.set(null);
    }
  }

  // ─── Relecture des propositions ─────────────────────────────────────────

  protected readonly aRefuser = signal<RessourceAdmin | null>(null);
  protected readonly motifRefus = signal('');
  protected readonly relectureEnCours = signal(false);
  protected readonly erreurRelecture = signal<string | null>(null);

  protected async publier(ressource: RessourceAdmin): Promise<void> {
    this.relectureEnCours.set(true);
    this.erreur.set(null);
    try {
      await this.administration.publierRessource(ressource.id);
      this.ressources.reload();
    } catch (e) {
      this.erreur.set((e as { error?: { detail?: string } })?.error?.detail ?? 'La publication a échoué. Réessayez dans un instant.');
    } finally {
      this.relectureEnCours.set(false);
    }
  }

  protected demanderRefus(ressource: RessourceAdmin): void {
    this.motifRefus.set('');
    this.erreurRelecture.set(null);
    this.aRefuser.set(ressource);
  }

  protected async refuser(): Promise<void> {
    const ressource = this.aRefuser();
    if (!ressource) return;
    if (this.motifRefus().trim().length < 10) {
      this.erreurRelecture.set('Expliquez le motif en 10 caractères au moins : le professionnel doit savoir quoi corriger.');
      return;
    }
    this.relectureEnCours.set(true);
    try {
      await this.administration.refuserRessource(ressource.id, this.motifRefus().trim());
      this.aRefuser.set(null);
      this.ressources.reload();
    } catch {
      this.erreurRelecture.set("Le refus n'a pas pu être enregistré. Réessayez dans un instant.");
    } finally {
      this.relectureEnCours.set(false);
    }
  }

  protected fermerRefus(ouverte: boolean): void {
    if (!ouverte) this.aRefuser.set(null);
  }

  protected async confirmerSuppression(): Promise<void> {
    const ressource = this.aSupprimer();
    if (!ressource) return;
    this.suppressionEnCours.set(true);
    try {
      await this.administration.supprimerRessource(ressource.id);
      this.suppressionOuverte.set(false);
      this.aSupprimer.set(null);
      this.ressources.reload();
    } catch {
      this.erreur.set('La suppression a échoué. Réessayez dans un instant.');
    } finally {
      this.suppressionEnCours.set(false);
    }
  }
}
