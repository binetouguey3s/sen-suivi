import { Injectable, WritableSignal, computed, inject, signal } from '@angular/core';

import { CompteService, Preferences } from '../../core/services/compte.service';
import { ConversationService } from '../../core/services/conversation.service';
import { ProfilOnboarding } from '../../core/models/onboarding';
import { MAX_PREOCCUPATIONS, PREOCCUPATIONS, SUGGESTIONS, Suggestion } from './onboarding.donnees';

// État partagé entre l'écran d'onboarding et ses étapes.
// Fourni au niveau du composant : il disparaît à la sortie de l'onboarding.
@Injectable()
export class OnboardingStore {
  private readonly compteService = inject(CompteService);
  private readonly conversation = inject(ConversationService);

  // Étape 1 : profil
  readonly prenom = signal(this.compteService.compte()?.prenom ?? '');
  readonly genre = signal<string | null>(null);
  readonly trancheAge = signal<string | null>(null);
  readonly situation = signal<string | null>(null);
  readonly langue = signal<string | null>('fr');

  // Étape 2 : humeur
  readonly humeur = signal<number | null>(null);
  readonly energie = signal(50);
  readonly sommeil = signal<string | null>(null);

  // Étape 3 : ce qui occupe l'esprit (3 sujets au plus)
  readonly preoccupations = signal<string[]>([]);
  readonly rienDeParticulier = signal(false);
  readonly maxAtteint = computed(() => this.preoccupations().length >= MAX_PREOCCUPATIONS);
  readonly libellesPreoccupations = computed(() =>
    this.preoccupations().map((v) => PREOCCUPATIONS.find((p) => p.valeur === v)?.libelle ?? v),
  );

  // Étape 4 : ce qui fait du bien
  readonly bienEtre = signal<string[]>([]);
  readonly spiritualite = signal<string[]>([]);

  // Étape 5 : rythme
  readonly moments = signal<string[]>([]);
  readonly duree = signal<string | null>(null);
  readonly formats = signal<string[]>([]);
  readonly rappels = signal(true);
  readonly frequenceRappels = signal('3_semaine');

  // Étape 6 : accompagnement et confidentialité
  readonly echangePro = signal<string | null>(null);
  readonly metiers = signal<string[]>([]);
  readonly aiseAvec = signal<string | null>(null);
  // Consentements : désactivés tant que l'utilisateur ne les active pas
  readonly personnalisation = signal(false);
  readonly conserverEchanges = signal(false);

  // Écran de présentation : explication « Pourquoi ces questions ? »
  readonly pourquoiOuvert = signal(false);

  readonly enregistrement = signal(false);
  readonly erreur = signal('');

  constructor() {
    // Juste après l'inscription, le compte n'est pas encore chargé : on récupère le prénom
    if (!this.compteService.compte()) {
      this.compteService
        .charger()
        .then((c) => {
          if (!this.prenom()) this.prenom.set(c.prenom ?? '');
        })
        .catch(() => undefined);
    }
  }

  // Écran final : trois ressources, les plus proches des réponses d'abord
  readonly suggestions = computed<Suggestion[]>(() => {
    const reponses = new Set([...this.preoccupations(), ...this.bienEtre(), ...this.moments()]);
    const score = (s: Suggestion) => s.pour.filter((p) => reponses.has(p)).length;
    return [...SUGGESTIONS].sort((a, b) => score(b) - score(a));
  });

  // ─── Sélections ──────────────────────────────────────────────────────────

  basculer(liste: WritableSignal<string[]>, valeur: string): void {
    liste.update((l) => (l.includes(valeur) ? l.filter((v) => v !== valeur) : [...l, valeur]));
  }

  basculerPreoccupation(valeur: string): void {
    const choisie = this.preoccupations().includes(valeur);
    if (!choisie && this.maxAtteint()) return;
    this.rienDeParticulier.set(false);
    this.basculer(this.preoccupations, valeur);
  }

  basculerRien(): void {
    const actif = !this.rienDeParticulier();
    this.rienDeParticulier.set(actif);
    if (actif) this.preoccupations.set([]);
  }

  // ─── Enregistrement ──────────────────────────────────────────────────────

  profil(statut: ProfilOnboarding['statut']): ProfilOnboarding {
    return {
      version: 1,
      statut,
      date: new Date().toISOString(),
      genre: this.genre() ?? undefined,
      tranche_age: this.trancheAge() ?? undefined,
      situation: this.situation() ?? undefined,
      langue: this.langue() ?? undefined,
      humeur: this.humeur() ?? undefined,
      energie: this.energie(),
      sommeil: this.sommeil() ?? undefined,
      preoccupations: this.preoccupations(),
      rien_de_particulier: this.rienDeParticulier(),
      bien_etre: this.bienEtre(),
      spiritualite: this.bienEtre().includes('spiritualite') ? this.spiritualite() : [],
      moments: this.moments(),
      duree: this.duree() ?? undefined,
      formats: this.formats(),
      rappels: this.rappels(),
      frequence_rappels: this.rappels() ? this.frequenceRappels() : undefined,
      echange_pro: this.echangePro() ?? undefined,
      metiers: this.echangePro() === 'pas_maintenant' ? [] : this.metiers(),
      aise_avec: this.aiseAvec() ?? undefined,
    };
  }

  // Fusionne avec les préférences existantes : le PATCH remplace tout le JSON,
  // il ne faut pas effacer les réglages de notifications déjà enregistrés.
  async enregistrer(statut: ProfilOnboarding['statut']): Promise<boolean> {
    this.enregistrement.set(true);
    this.erreur.set('');
    try {
      const compte = this.compteService.compte() ?? (await this.compteService.charger());
      const preferences: Preferences = {
        ...compte.preferences,
        onboarding: this.profil(statut),
      };
      if (statut === 'termine') preferences.personnalisation_chatbot = this.personnalisation();

      const prenom = this.prenom().trim();
      await this.compteService.modifier({
        preferences,
        ...(statut === 'termine' && prenom && prenom !== compte.prenom ? { prenom } : {}),
      });
      if (statut === 'termine' && this.conserverEchanges()) {
        await this.conversation.definirConservation(true);
      }
      return true;
    } catch {
      this.erreur.set('Tes réponses n’ont pas pu être enregistrées. Vérifie ta connexion et réessaie.');
      return false;
    } finally {
      this.enregistrement.set(false);
    }
  }
}
