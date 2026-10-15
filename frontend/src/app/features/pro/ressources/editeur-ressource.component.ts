import { httpResource } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { Ressource, StatutRessource, TypeRessource } from '../../../core/models/suivi';
import { AuthService } from '../../../core/services/auth.service';
import { BrouillonRessource, RessourcesProService } from '../../../core/services/ressources-pro.service';
import { valeurs } from '../../../core/utils/ressource';
import { CarteRessourceComponent } from '../../../shared/carte-ressource/carte-ressource.component';
import { erreurFichierAudio } from '../../../shared/champ-audio/champ-audio.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { VideoYoutubeComponent, idYoutube } from '../../../shared/video-youtube/video-youtube.component';
import { FORMATS, STATUTS, THEMATIQUES_PAR_DEFAUT, assemblerContenu, separerChapo } from './ressources-pro';

export const TITRE_MAX = 120;
export const TITRE_MIN = 8;
export const CHAPO_MAX = 280;
// Sauvegarde automatique du brouillon, s'il a changé
export const INTERVALLE_SAUVEGARDE = 20_000;

const STATUTS_MODIFIABLES: StatutRessource[] = ['BROUILLON', 'REFUSEE'];

interface ProfilPro {
  nom: string;
  specialite_affichee: string;
}

// Éditeur d'une ressource proposée (/pro/ressources/nouvelle et
// /pro/ressources/:id/modifier), d'après la maquette validée : formulaire en
// 5 blocs, aperçu de la carte de la bibliothèque mis à jour en direct.
@Component({
  selector: 'ss-editeur-ressource',
  standalone: true,
  imports: [RouterLink, IconComponent, ModalComponent, CarteRessourceComponent, VideoYoutubeComponent],
  templateUrl: './editeur-ressource.component.html',
  styleUrl: './editeur-ressource.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditeurRessourceComponent {
  private readonly service = inject(RessourcesProService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  // Paramètre de route :id (absent pour une nouvelle ressource)
  readonly id = input<string>();

  protected readonly formats = FORMATS;
  protected readonly titreMax = TITRE_MAX;
  protected readonly chapoMax = CHAPO_MAX;

  // ─── Données chargées ────────────────────────────────────────────────────

  private readonly existante = httpResource<Ressource>(() => (this.id() ? `${API_BASE_URL}/pro/ressources/${this.id()}` : undefined));
  private readonly publiees = httpResource<Ressource[]>(() => `${API_BASE_URL}/ressources`, { defaultValue: [] });
  private readonly profil = httpResource<ProfilPro>(() => {
    const id = this.auth.identifiant();
    return id ? `${API_BASE_URL}/professionnels/${id}` : undefined;
  });

  // Les mêmes thématiques que la bibliothèque
  protected readonly thematiques = computed(() => {
    const existantes = [...new Set(valeurs(this.publiees).map((r) => r.thematique))];
    return (existantes.length ? existantes : THEMATIQUES_PAR_DEFAUT).sort((a, b) => a.localeCompare(b, 'fr'));
  });

  // ─── Formulaire ──────────────────────────────────────────────────────────

  protected readonly ressourceId = signal<number | null>(null);
  protected readonly statut = signal<StatutRessource>('BROUILLON');
  protected readonly motifRefus = signal('');
  protected readonly typeRessource = signal<TypeRessource>('ARTICLE');
  protected readonly titre = signal('');
  protected readonly thematique = signal('');
  protected readonly chapo = signal('');
  protected readonly duree = signal(5);
  protected readonly texte = signal('');
  protected readonly lienVideo = signal('');
  protected readonly charte = signal(false);

  // Audio : celui déjà enregistré, celui en cours d'envoi
  protected readonly audioActuel = signal<string | null>(null);
  protected readonly fichierAudio = signal<{ nom: string; taille: number } | null>(null);
  protected readonly progression = signal<number | null>(null);
  protected readonly erreurAudio = signal<string | null>(null);

  protected readonly modifie = signal(false);
  protected readonly enregistrement = signal(false);
  protected readonly derniereSauvegarde = signal<Date | null>(null);
  protected readonly erreur = signal<string | null>(null);

  private readonly champTexte = viewChild<ElementRef<HTMLTextAreaElement>>('champTexte');

  protected readonly modifiable = computed(() => STATUTS_MODIFIABLES.includes(this.statut()));
  protected readonly chargement = computed(() => !!this.id() && this.existante.isLoading());
  protected readonly introuvable = computed(() => !!this.id() && !!this.existante.error());
  protected readonly libelleStatut = computed(() => STATUTS[this.statut()].libelle);

  protected readonly videoId = computed(() => idYoutube(this.lienVideo()));
  protected readonly aUnAudio = computed(() => !!this.audioActuel());

  // ─── Soumission : ce qui manque, dit précisément ─────────────────────────

  protected readonly manque = computed<string | null>(() => {
    if (this.titre().trim().length < TITRE_MIN) return 'Ajoutez un titre (8 caractères au moins).';
    if (!this.thematique()) return 'Choisissez une thématique.';
    if (this.typeRessource() === 'VIDEO' && !this.videoId()) return 'Ajoutez un lien YouTube valide.';
    if (this.typeRessource() === 'PODCAST' && !this.aUnAudio()) return 'Ajoutez votre fichier audio.';
    if (!this.texte().trim() && !this.chapo().trim()) return 'Écrivez le contenu de la ressource.';
    if (!this.charte()) return 'Cochez l’engagement pour soumettre.';
    return null;
  });
  protected readonly soumissionPossible = computed(() => !this.manque() && !this.enregistrement() && this.progression() === null);

  // ─── Aperçu : la carte telle qu'elle apparaîtra dans la bibliothèque ─────

  protected readonly apercu = computed<Ressource>(() => {
    const profil = this.profil.hasValue() ? this.profil.value() : null;
    return {
      id: this.ressourceId() ?? 0,
      titre: this.titre().trim() || 'Titre de votre ressource',
      type_ressource: this.typeRessource(),
      thematique: this.thematique() || 'Thématique',
      contenu: assemblerContenu(this.chapo() || 'Votre chapô apparaîtra ici.', this.texte()),
      duree_lecture: this.duree() || 1,
      date_publication: new Date().toISOString().slice(0, 10),
      auteur: { id: this.auth.identifiant() ?? 0, nom: profil?.nom ?? this.auth.nom() ?? '', specialite_affichee: profil?.specialite_affichee ?? '' },
    };
  });

  // Parcours de validation : l'étape où en est la ressource
  protected readonly etapeActuelle = computed(() => (this.statut() === 'EN_ATTENTE' ? 1 : this.statut() === 'PUBLIEE' ? 2 : 0));

  // Quitter avec des modifications : on propose d'enregistrer d'abord
  protected readonly confirmationSortie = signal(false);
  private resoudreSortie: ((quitter: boolean) => void) | null = null;

  constructor() {
    // Une ressource existante remplit le formulaire une fois chargée
    effect(() => {
      if (!this.existante.hasValue()) return;
      const r = this.existante.value();
      untracked(() => this.remplir(r));
    });

    const minuterie = setInterval(() => {
      if (this.modifie() && this.modifiable() && !this.enregistrement() && this.progression() === null) {
        void this.enregistrerBrouillon();
      }
    }, INTERVALLE_SAUVEGARDE);
    inject(DestroyRef).onDestroy(() => clearInterval(minuterie));
  }

  private remplir(r: Ressource): void {
    const { chapo, texte } = separerChapo(r.contenu);
    this.ressourceId.set(r.id);
    this.statut.set(r.statut ?? 'BROUILLON');
    this.motifRefus.set(r.motif_refus ?? '');
    this.typeRessource.set(r.type_ressource);
    this.titre.set(r.titre);
    this.thematique.set(r.thematique);
    this.chapo.set(chapo);
    this.texte.set(texte);
    this.duree.set(r.duree_lecture);
    this.lienVideo.set(r.url_video ?? '');
    this.audioActuel.set(r.audio || null);
    this.modifie.set(false);
  }

  // Toute saisie marque le brouillon comme modifié
  protected changer<T>(champ: { set(valeur: T): void }, valeur: T): void {
    champ.set(valeur);
    this.modifie.set(true);
  }

  protected saisirDuree(evenement: Event): void {
    const valeur = Math.round(Number((evenement.target as HTMLInputElement).value));
    this.changer(this.duree, Math.min(120, Math.max(1, valeur || 1)));
  }

  // Raccourcis de mise en forme : « ## », « > », « - » à la position du curseur
  protected inserer(marque: string): void {
    const champ = this.champTexte()?.nativeElement;
    const texte = this.texte();
    const position = champ?.selectionEnd ?? texte.length;
    const avant = texte.slice(0, position);
    const prefixe = avant && !avant.endsWith('\n') ? '\n' : '';
    const insertion = `${prefixe}${marque} `;
    this.changer(this.texte, avant + insertion + texte.slice(position));
    if (champ) {
      champ.value = this.texte();
      champ.focus();
      champ.selectionStart = champ.selectionEnd = position + insertion.length;
    }
  }

  // ─── Enregistrement ──────────────────────────────────────────────────────

  private donnees(): BrouillonRessource {
    return {
      titre: this.titre().trim(),
      type_ressource: this.typeRessource(),
      thematique: this.thematique(),
      contenu: assemblerContenu(this.chapo(), this.texte()),
      duree_lecture: this.duree(),
      url_video: this.typeRessource() === 'VIDEO' ? this.lienVideo().trim() : '',
    };
  }

  // Crée le brouillon au premier enregistrement, puis le met à jour
  protected async enregistrerBrouillon(): Promise<boolean> {
    this.enregistrement.set(true);
    this.erreur.set(null);
    try {
      const id = this.ressourceId();
      const r = id ? await this.service.modifier(id, this.donnees()) : await this.service.creer(this.donnees());
      this.ressourceId.set(r.id);
      this.statut.set(r.statut ?? 'BROUILLON');
      this.modifie.set(false);
      this.derniereSauvegarde.set(new Date());
      return true;
    } catch (e) {
      const detail = (e as { error?: Record<string, unknown> })?.error;
      this.erreur.set(
        detail && 'url_video' in detail
          ? 'Seuls les liens YouTube sont acceptés.'
          : 'Le brouillon n’a pas pu être enregistré. Vérifiez votre connexion et réessayez.',
      );
      return false;
    } finally {
      this.enregistrement.set(false);
    }
  }

  protected heureSauvegarde(): string {
    const d = this.derniereSauvegarde();
    return d ? d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '';
  }

  protected async soumettre(evenement?: Event): Promise<void> {
    evenement?.preventDefault();
    if (!this.soumissionPossible()) return;
    if (!(await this.enregistrerBrouillon())) return;
    this.enregistrement.set(true);
    try {
      await this.service.soumettre(this.ressourceId()!);
      this.modifie.set(false);
      await this.router.navigateByUrl('/pro/ressources');
    } catch (e) {
      this.erreur.set((e as { error?: { detail?: string } })?.error?.detail ?? 'La soumission a échoué. Réessayez dans un instant.');
    } finally {
      this.enregistrement.set(false);
    }
  }

  // ─── Fichier audio (podcast) ─────────────────────────────────────────────

  protected choisirFichier(evenement: Event): void {
    const champ = evenement.target as HTMLInputElement;
    void this.envoyerAudio(champ.files?.[0] ?? null);
    champ.value = '';
  }

  protected deposer(evenement: DragEvent): void {
    evenement.preventDefault();
    void this.envoyerAudio(evenement.dataTransfer?.files?.[0] ?? null);
  }

  protected async envoyerAudio(fichier: File | null): Promise<void> {
    if (!fichier) return;
    const erreur = erreurFichierAudio(fichier);
    if (erreur) {
      this.erreurAudio.set(erreur.startsWith('Le fichier dépasse') ? 'Fichier trop lourd (20 Mo au plus).' : 'Format non accepté : MP3, M4A ou OGG.');
      return;
    }
    this.erreurAudio.set(null);
    // Le fichier rejoint un brouillon : on l'enregistre d'abord s'il n'existe pas encore
    if (!this.ressourceId() && !(await this.enregistrerBrouillon())) return;
    this.fichierAudio.set({ nom: fichier.name, taille: fichier.size });
    this.progression.set(0);
    try {
      const r = await this.service.envoyerAudio(this.ressourceId()!, fichier, (p) => this.progression.set(p));
      this.audioActuel.set(r.audio || null);
    } catch {
      this.erreurAudio.set('Le fichier n’a pas pu être envoyé. Vérifiez qu’il s’agit bien d’un enregistrement audio, puis réessayez.');
      this.fichierAudio.set(null);
    } finally {
      this.progression.set(null);
    }
  }

  protected tailleMo(octets: number): string {
    return `${(octets / (1024 * 1024)).toFixed(1).replace('.', ',')} Mo`;
  }

  // ─── Sortie de la page ───────────────────────────────────────────────────

  // Appelé par le garde de route : true si l'on peut quitter
  peutQuitter(): boolean | Promise<boolean> {
    if (!this.modifie() || !this.modifiable()) return true;
    this.confirmationSortie.set(true);
    return new Promise((resoudre) => (this.resoudreSortie = resoudre));
  }

  protected async repondreSortie(choix: 'enregistrer' | 'quitter' | 'rester'): Promise<void> {
    if (choix === 'enregistrer' && !(await this.enregistrerBrouillon())) return;
    this.confirmationSortie.set(false);
    if (choix !== 'rester') this.modifie.set(false);
    this.resoudreSortie?.(choix !== 'rester');
    this.resoudreSortie = null;
  }
}
