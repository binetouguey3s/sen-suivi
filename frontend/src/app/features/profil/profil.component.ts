import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  computed,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';

import { VILLES_SENEGAL } from '../../core/models/comptes';
import { NomIcone } from '../../core/icons/icons';
import { ProfilOnboarding } from '../../core/models/onboarding';
import { ErreurFormulaire } from '../../core/services/auth.service';
import { CompteService, Preferences } from '../../core/services/compte.service';
import { ConversationService } from '../../core/services/conversation.service';
import { ChampComponent } from '../../shared/champ/champ.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { InterrupteurComponent } from '../../shared/interrupteur/interrupteur.component';
import { ModalComponent } from '../../shared/modal/modal.component';
import { EtapeAccompagnementComponent } from '../onboarding/etapes/etape-accompagnement.component';
import { EtapeBienEtreComponent } from '../onboarding/etapes/etape-bien-etre.component';
import { EtapeEspritComponent } from '../onboarding/etapes/etape-esprit.component';
import { EtapeProfilComponent } from '../onboarding/etapes/etape-profil.component';
import { EtapeRythmeComponent } from '../onboarding/etapes/etape-rythme.component';
import {
  AISANCES,
  BIEN_ETRE,
  Choix,
  DUREES,
  FORMATS,
  FREQUENCES,
  GENRES,
  LANGUES,
  METIERS,
  MOMENTS,
  PREOCCUPATIONS,
  SITUATIONS,
  SPIRITUALITE,
  TRANCHES_AGE,
} from '../onboarding/onboarding.donnees';
import { OnboardingStore } from '../onboarding/onboarding.store';

// Les cinq sections du profil bien-être, dans l'ordre de l'onboarding
export type Section = 'profil' | 'esprit' | 'bien-etre' | 'rythme' | 'accompagnement';

interface InfoSection {
  titre: string;
  icone: NomIcone;
}

const SECTIONS: Record<Section, InfoSection> = {
  profil: { titre: 'À propos de moi', icone: 'utilisateur' },
  esprit: { titre: 'Ce qui m’occupe l’esprit', icone: 'suggestion' },
  'bien-etre': { titre: 'Ce qui me fait du bien', icone: 'coeur' },
  rythme: { titre: 'Mon rythme', icone: 'horloge' },
  accompagnement: { titre: 'Accompagnement', icone: 'accompagnement' },
};
const ORDRE_SECTIONS = Object.keys(SECTIONS) as Section[];

// Durée d'affichage du « Enregistré » discret après un changement
const DUREE_CONFIRMATION = 3000;

// Libellé d'une valeur enregistrée : jamais le code (« etudiant », « COACH_SPORTIF »)
function libelle(liste: readonly Choix[], valeur: string | undefined): string | null {
  return valeur ? (liste.find((c) => c.valeur === valeur)?.libelle ?? null) : null;
}

function libelles(liste: readonly Choix[], valeurs: readonly string[] | undefined): string[] {
  return (valeurs ?? []).map((v) => libelle(liste, v)).filter((l): l is string => !!l);
}

function minuscule(texte: string): string {
  return texte.charAt(0).toLowerCase() + texte.slice(1);
}

// Une section est remplie dès qu'une de ses questions a une réponse
function remplie(section: Section, p: ProfilOnboarding): boolean {
  switch (section) {
    case 'profil':
      return !!(p.genre || p.tranche_age || p.situation || p.langue);
    case 'esprit':
      return (p.preoccupations?.length ?? 0) > 0 || p.rien_de_particulier;
    case 'bien-etre':
      return (p.bien_etre?.length ?? 0) > 0;
    case 'rythme':
      return (p.moments?.length ?? 0) > 0 || !!p.duree || (p.formats?.length ?? 0) > 0;
    case 'accompagnement':
      return !!p.echange_pro || (p.metiers?.length ?? 0) > 0;
  }
}

// Page « Mon profil » de l'espace utilisateur (/app/profil) : ce que la personne
// a dit d'elle à l'inscription et dans l'onboarding, modifiable section par
// section avec les écrans mêmes de l'onboarding, et effaçable.
@Component({
  selector: 'ss-profil',
  standalone: true,
  imports: [
    NgTemplateOutlet,
    RouterLink,
    ChampComponent,
    IconComponent,
    InterrupteurComponent,
    ModalComponent,
    EtapeProfilComponent,
    EtapeEspritComponent,
    EtapeBienEtreComponent,
    EtapeRythmeComponent,
    EtapeAccompagnementComponent,
  ],
  providers: [OnboardingStore],
  templateUrl: './profil.component.html',
  styleUrl: './profil.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown.escape)': 'fermerTout()' },
})
export class ProfilComponent {
  private readonly compteService = inject(CompteService);
  protected readonly conversation = inject(ConversationService);
  protected readonly store = inject(OnboardingStore);

  protected info(section: Section): InfoSection {
    return SECTIONS[section];
  }
  protected readonly villes = VILLES_SENEGAL;

  protected readonly compte = this.compteService.compte;
  protected readonly erreurChargement = signal(false);

  // Annonce pour les lecteurs d'écran après un enregistrement (réussi ou non)
  protected readonly annonce = signal('');
  // « Enregistré » discret à côté des choix de confidentialité
  protected readonly confirmation = signal(false);
  private minuterie: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    this.compteService.charger().catch(() => this.erreurChargement.set(!this.compte()));
    inject(DestroyRef).onDestroy(() => clearTimeout(this.minuterie));

    // À l'ouverture d'une section, le focus va sur son titre (lu par le lecteur d'écran)
    effect(() => {
      if (!this.sectionOuverte()) return;
      const zone = this.zoneSection()?.nativeElement;
      queueMicrotask(() => zone?.querySelector<HTMLElement>('h1')?.focus());
    });
  }

  // ─── Identité ────────────────────────────────────────────────────────────

  protected readonly prenom = computed(() => this.compte()?.prenom?.trim() || this.compte()?.nom || '');
  protected readonly initiales = computed(() => {
    const c = this.compte();
    return `${c?.prenom?.[0] ?? ''}${c?.nom?.[0] ?? ''}`.toUpperCase() || '?';
  });

  // ─── Profil bien-être ────────────────────────────────────────────────────

  protected readonly onboarding = computed(() => this.compte()?.preferences?.onboarding);
  // Onboarding passé ou jamais fait : l'état vide invite à faire connaissance
  protected readonly rempli = computed(() => this.onboarding()?.statut === 'termine');

  protected readonly sectionsRemplies = computed(() => {
    const p = this.onboarding();
    return new Set(p ? ORDRE_SECTIONS.filter((s) => remplie(s, p)) : []);
  });
  protected readonly pourcentage = computed(() => Math.round((this.sectionsRemplies().size / ORDRE_SECTIONS.length) * 100));
  protected readonly premiereVide = computed(() => ORDRE_SECTIONS.find((s) => !this.sectionsRemplies().has(s)) ?? null);

  protected readonly aPropos = computed(() => {
    const p = this.onboarding();
    return [
      { libelle: 'Genre', valeur: libelle(GENRES, p?.genre) },
      { libelle: 'Âge', valeur: libelle(TRANCHES_AGE, p?.tranche_age) },
      { libelle: 'Situation', valeur: libelle(SITUATIONS, p?.situation) },
      { libelle: 'Langue', valeur: libelle(LANGUES, p?.langue) },
    ];
  });

  protected readonly preoccupations = computed(() => libelles(PREOCCUPATIONS, this.onboarding()?.preoccupations));

  protected readonly bienEtre = computed(() =>
    (this.onboarding()?.bien_etre ?? [])
      .map((v) => BIEN_ETRE.find((c) => c.valeur === v))
      .filter((c): c is Choix => !!c),
  );
  protected readonly spiritualite = computed(() => libelles(SPIRITUALITE, this.onboarding()?.spiritualite).join(', '));

  protected readonly moments = computed(() => libelles(MOMENTS, this.onboarding()?.moments));
  // « 5–10 min par jour · Audio, Exercice guidé »
  protected readonly dureeEtFormats = computed(() => {
    const p = this.onboarding();
    const duree = libelle(DUREES, p?.duree);
    const formats = libelles(FORMATS, p?.formats).join(', ');
    return [duree && `${duree} par jour`, formats].filter(Boolean).join(' · ');
  });
  protected readonly rappels = computed(() => {
    const p = this.onboarding();
    const frequence = libelle(FREQUENCES, p?.frequence_rappels);
    if (!p?.rappels || !frequence || p.frequence_rappels === 'jamais') return 'Rappels désactivés';
    return `Rappels ${minuscule(frequence)}`;
  });

  protected readonly envieEchange = computed(() => {
    switch (this.onboarding()?.echange_pro) {
      case 'oui':
        return 'Vous aimeriez échanger avec un professionnel.';
      case 'plus_tard':
        return 'Un échange avec un professionnel, peut-être plus tard.';
      case 'pas_maintenant':
        return 'Pas d’échange avec un professionnel pour l’instant.';
      default:
        return null;
    }
  });
  protected readonly metiers = computed(() => libelles(METIERS, this.onboarding()?.metiers));
  protected readonly aiseAvec = computed(() => {
    const valeur = this.onboarding()?.aise_avec;
    if (valeur === 'indifferent') return 'Une femme ou un homme : peu importe';
    const choix = libelle(AISANCES, valeur);
    return choix ? `Plus à l’aise avec ${minuscule(choix)}` : null;
  });

  // ─── Modification d'une section ──────────────────────────────────────────

  protected readonly sectionOuverte = signal<Section | null>(null);
  private readonly zoneSection = viewChild<ElementRef<HTMLElement>>('zoneSection');

  // Chaque ouverture repart des réponses enregistrées : « Annuler » ne laisse aucune trace
  protected ouvrir(section: Section): void {
    const p = this.onboarding();
    if (p) this.store.hydrater(p);
    this.store.erreur.set('');
    this.sectionOuverte.set(section);
  }

  protected async enregistrerSection(): Promise<void> {
    const section = this.sectionOuverte();
    if (!section) return;
    if (await this.store.enregistrerReponses()) {
      this.sectionOuverte.set(null);
      this.annonce.set(`« ${SECTIONS[section].titre} » est enregistré.`);
    } else {
      this.annonce.set(this.store.erreur());
    }
  }

  // ─── Prénom et ville ─────────────────────────────────────────────────────

  protected readonly infosOuvertes = signal(false);
  protected readonly prenomSaisi = signal('');
  protected readonly villeSaisie = signal('');
  protected readonly erreursInfos = signal<Record<string, string>>({});
  protected readonly enregistrementInfos = signal(false);

  protected ouvrirInfos(): void {
    this.prenomSaisi.set(this.compte()?.prenom ?? '');
    this.villeSaisie.set(this.compte()?.ville ?? '');
    this.erreursInfos.set({});
    this.infosOuvertes.set(true);
  }

  protected async enregistrerInfos(evenement: Event): Promise<void> {
    evenement.preventDefault();
    this.enregistrementInfos.set(true);
    try {
      await this.compteService.modifier({ prenom: this.prenomSaisi().trim(), ville: this.villeSaisie() || null });
      this.infosOuvertes.set(false);
      this.annonce.set('Vos informations sont enregistrées.');
    } catch (e) {
      this.erreursInfos.set(e instanceof ErreurFormulaire ? e.champs : {});
      this.annonce.set('Vos informations n’ont pas pu être enregistrées.');
    } finally {
      this.enregistrementInfos.set(false);
    }
  }

  // ─── Confidentialité ─────────────────────────────────────────────────────

  // Consentement explicite : désactivé tant que la personne ne l'a pas activé
  protected readonly personnalisation = computed(() => this.compte()?.preferences?.personnalisation_chatbot === true);
  protected readonly erreurConfidentialite = signal(false);

  protected async basculerPersonnalisation(valeur: boolean): Promise<void> {
    const c = this.compte();
    if (!c) return;
    const preferences: Preferences = { ...c.preferences, personnalisation_chatbot: valeur };
    // Affichage immédiat, annulé si le serveur refuse
    this.compteService.compte.set({ ...c, preferences });
    try {
      await this.compteService.modifier({ preferences });
      this.confirmer();
    } catch {
      this.compteService.compte.set(c);
      this.echecConfidentialite();
    }
  }

  protected async basculerConservation(valeur: boolean): Promise<void> {
    await this.conversation.definirConservation(valeur);
    if (this.conversation.erreurConservation()) this.echecConfidentialite();
    else this.confirmer();
  }

  private confirmer(): void {
    this.erreurConfidentialite.set(false);
    this.confirmation.set(true);
    this.annonce.set('Votre choix est enregistré.');
    clearTimeout(this.minuterie);
    this.minuterie = setTimeout(() => this.confirmation.set(false), DUREE_CONFIRMATION);
  }

  private echecConfidentialite(): void {
    this.confirmation.set(false);
    this.erreurConfidentialite.set(true);
    this.annonce.set('Votre choix n’a pas pu être enregistré.');
  }

  // ─── Mes données ─────────────────────────────────────────────────────────

  protected readonly confirmationEffacer = signal(false);
  protected readonly effacement = signal(false);
  protected readonly erreurEffacer = signal(false);

  // Seules les réponses de l'onboarding partent : notifications et consentements restent
  protected async effacer(): Promise<void> {
    const c = this.compte();
    if (!c) return;
    const { onboarding: _efface, ...preferences } = c.preferences;
    this.effacement.set(true);
    this.erreurEffacer.set(false);
    try {
      await this.compteService.modifier({ preferences });
      this.confirmationEffacer.set(false);
      this.annonce.set('Vos réponses ont été effacées.');
    } catch {
      this.erreurEffacer.set(true);
    } finally {
      this.effacement.set(false);
    }
  }

  protected fermerTout(): void {
    this.sectionOuverte.set(null);
    this.infosOuvertes.set(false);
    this.confirmationEffacer.set(false);
  }
}
