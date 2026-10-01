import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, afterNextRender, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { DIAPOS_BANDEAU, DUREE_DIAPO_MS, IMAGES_ACCUEIL } from '../../core/config/images-accueil';
import { imageDuLieu } from '../../core/config/images-lieux';
import { IMAGE_PAR_PROFESSIONNEL } from '../../core/config/images-professionnels';
import { NomIcone } from '../../core/icons/icons';
import { LieuDetente } from '../../core/models/suivi';
import { AuthService } from '../../core/services/auth.service';
import { valeurs } from '../../core/utils/ressource';
import { IconComponent } from '../../shared/icon/icon.component';

interface ProfessionnelPublic {
  id: number;
  nom: string;
  specialite_affichee: string;
  presentation: string;
}

interface Temoignage {
  id: number;
  contenu: string;
  pseudonyme: string;
  anciennete: string;
}

const LONGUEUR_CITATION = 110;

@Component({
  selector: 'ss-accueil',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './accueil.component.html',
  styleUrl: './accueil.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccueilComponent {
  protected readonly auth = inject(AuthService);
  protected readonly images = IMAGES_ACCUEIL;

  // Bandeau d'ouverture : les photos se succèdent en fondu. Défilement
  // suspendu par le bouton pause (WCAG 2.2.2) et jamais lancé quand
  // l'utilisateur préfère réduire les animations.
  protected readonly diapos = DIAPOS_BANDEAU;
  protected readonly diapo = signal(0);
  protected readonly enPause = signal(false);
  protected readonly defilementPossible = signal(false);

  constructor() {
    this.lancerDiaporama();
  }

  protected readonly confiance: { icone: NomIcone; libelle: string }[] = [
    { icone: 'cadenas', libelle: 'Pseudonyme sur le forum' },
    { icone: 'utilisateur-verifie', libelle: 'Experts sénégalais' },
    { icone: 'horloge', libelle: 'Accès 24h/24' },
    { icone: 'globe', libelle: 'Approche culturelle' },
  ];

  protected readonly engagements: { icone: NomIcone; titre: string; texte: string }[] = [
    { icone: 'cadenas', titre: 'Accès limité', texte: 'Seuls les membres ont accès à votre espace personnel sécurisé.' },
    { icone: 'coeur', titre: 'Espace sans jugement', texte: 'Exprimez-vous librement, nous sommes là pour vous comprendre.' },
    { icone: 'horloge', titre: 'Écoute à toute heure', texte: 'Des ressources et un chatbot disponibles 24h/24, 7j/7.' },
  ];

  protected readonly evaluations: { type: string; cle: 'stress' | 'anxiete' | 'fatigue'; titre: string; texte: string }[] = [
    { type: 'STRESS', cle: 'stress', titre: 'Stress', texte: 'Évaluez votre niveau de tension quotidienne.' },
    { type: 'ANXIETE', cle: 'anxiete', titre: 'Anxiété', texte: "Identifiez les signes d'inquiétude excessive." },
    { type: 'FATIGUE', cle: 'fatigue', titre: 'Fatigue', texte: 'Mesurez votre fatigue émotionnelle et physique.' },
  ];

  protected readonly etapes: { titre: string; texte: string }[] = [
    { titre: 'Inscription', texte: 'Créez votre profil en quelques secondes.' },
    { titre: 'Auto-évaluation', texte: 'Répondez à quelques questions pour situer votre état.' },
    { titre: 'Accompagnement', texte: 'Échangez avec nos experts ou discutez avec Titou.' },
    { titre: 'Sérénité', texte: 'Suivez vos progrès et retrouvez votre équilibre.' },
  ];

  private readonly tousLesLieux = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, { defaultValue: [] });
  private readonly tousLesPros = httpResource<ProfessionnelPublic[]>(() => `${API_BASE_URL}/professionnels/valides`, {
    defaultValue: [],
  });
  // Témoignages publiés avec l'accord de leur auteur, après modération
  private readonly tousLesTemoignages = httpResource<Temoignage[]>(() => `${API_BASE_URL}/temoignages`, {
    defaultValue: [],
  });

  // Uniquement les lieux dont on dispose d'une vraie photo
  protected readonly lieux = computed(() =>
    valeurs(this.tousLesLieux).filter((l) => imageDuLieu(l.nom) !== null).slice(0, 4),
  );

  protected readonly specialite = signal<string | null>(null);
  // Filtres construits à partir des spécialités réellement présentes
  protected readonly specialites = computed(() => [
    ...new Set(valeurs(this.tousLesPros).map((p) => p.specialite_affichee)),
  ]);
  protected readonly professionnels = computed(() => {
    const choix = this.specialite();
    return valeurs(this.tousLesPros)
      .filter((p) => !choix || p.specialite_affichee === choix)
      .slice(0, 3);
  });

  protected readonly temoignages = computed(() => valeurs(this.tousLesTemoignages).slice(0, 3));

  // Destination des boutons d'inscription : l'espace du compte s'il est connecté
  protected readonly destinationCompte = computed(() =>
    this.auth.estConnecte() ? this.auth.espaceAccueil() : '/inscription',
  );

  protected imageLieu(lieu: LieuDetente): string {
    return imageDuLieu(lieu.nom) ?? '';
  }

  protected portrait(pro: ProfessionnelPublic): string | null {
    return IMAGE_PAR_PROFESSIONNEL[pro.nom] ?? null;
  }

  protected initiales(nom: string): string {
    return nom.split(/\s+/).slice(0, 2).map((m) => m[0]).join('').toUpperCase();
  }

  protected citation(pro: ProfessionnelPublic): string | null {
    const texte = pro.presentation.trim();
    if (!texte) return null;
    return texte.length > LONGUEUR_CITATION ? `${texte.slice(0, LONGUEUR_CITATION).trimEnd()}…` : texte;
  }

  protected basculerPause(): void {
    this.enPause.update((pause) => !pause);
  }

  private lancerDiaporama(): void {
    const destruction = inject(DestroyRef);
    // Navigateur uniquement : afterNextRender ne s'exécute jamais côté serveur
    afterNextRender(() => {
      const mouvementReduit = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
      if (this.diapos.length < 2 || mouvementReduit) return;
      this.defilementPossible.set(true);
      const minuterie = setInterval(() => {
        if (!this.enPause()) this.diapo.update((i) => (i + 1) % this.diapos.length);
      }, DUREE_DIAPO_MS);
      destruction.onDestroy(() => clearInterval(minuterie));
    });
  }
}
