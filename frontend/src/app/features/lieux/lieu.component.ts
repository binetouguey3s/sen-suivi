import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnDestroy, computed, effect, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { imageDuLieu } from '../../core/config/images-lieux';
import { ACCES_PAR_CODE, CATEGORIE_PAR_NOM, MENTION_TARIFS, NOTE_DPN } from '../../core/config/lieux';
import { LieuDetente } from '../../core/models/suivi';
import { AuthService } from '../../core/services/auth.service';
import { lienCarte, lienItineraire, suggestionsPour } from '../../core/utils/lieux';
import { valeurs } from '../../core/utils/ressource';
import { CarteLieuComponent } from '../../shared/carte-lieu/carte-lieu.component';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { CouvertureLieuComponent } from '../../shared/couverture-lieu/couverture-lieu.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { ModalUrgenceComponent } from '../../shared/modal-urgence/modal-urgence.component';
import { PastilleAccesComponent } from '../../shared/pastille-acces/pastille-acces.component';

@Component({
  selector: 'ss-lieu',
  standalone: true,
  imports: [
    RouterLink,
    IconComponent,
    CarteLieuxComponent,
    CarteLieuComponent,
    CouvertureLieuComponent,
    ModalUrgenceComponent,
    PastilleAccesComponent,
  ],
  templateUrl: './lieu.component.html',
  styleUrl: './lieu.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LieuComponent implements OnDestroy {
  // Paramètre de route :id (withComponentInputBinding)
  readonly id = input.required<string>();

  private readonly auth = inject(AuthService);

  protected readonly mentionTarifs = MENTION_TARIFS;
  protected readonly noteDpn = NOTE_DPN;

  protected readonly lieu = httpResource<LieuDetente>(() => `${API_BASE_URL}/lieux/${this.id()}`);

  private readonly lieuCourant = computed(() => (this.lieu.hasValue() ? this.lieu.value() : null));

  // Les lieux de sa région, une fois le lieu connu
  private readonly voisins = httpResource<LieuDetente[]>(
    () => {
      const l = this.lieuCourant();
      return l ? `${API_BASE_URL}/lieux?region=${encodeURIComponent(l.region)}` : undefined;
    },
    { defaultValue: [] },
  );

  protected readonly modaleUrgenceOuverte = signal(false);
  protected readonly messagePartage = signal('');
  private minuteurPartage: ReturnType<typeof setTimeout> | undefined;

  protected readonly image = computed(() => {
    const l = this.lieuCourant();
    return l ? imageDuLieu(l) : null;
  });

  protected readonly estAdministrateur = computed(() => this.auth.typeCompte() === 'administrateur');

  protected readonly categorie = computed(() => {
    const l = this.lieuCourant();
    return l ? CATEGORIE_PAR_NOM.get(l.categorie) : undefined;
  });

  protected readonly iconeCategorie = computed(() => this.categorie()?.icone ?? 'lieux');

  protected readonly itineraire = computed(() => {
    const l = this.lieuCourant();
    return l ? lienItineraire(l) : '';
  });

  protected readonly carteGoogle = computed(() => {
    const l = this.lieuCourant();
    return l ? lienCarte(l) : '';
  });

  // « Lieux › Dakar › Dakar » n'apporte rien : la localité ne s'affiche que si elle diffère
  protected readonly localiteDistincte = computed(() => {
    const l = this.lieuCourant();
    return !!l && l.ville.trim().toLowerCase() !== l.region.trim().toLowerCase();
  });

  protected readonly libelleAcces = computed(() => {
    const l = this.lieuCourant();
    return l ? ACCES_PAR_CODE.get(l.acces)?.libelle : '';
  });

  protected readonly estRestreint = computed(() => this.lieuCourant()?.acces === 'RESTREINT');

  protected readonly avecBandeau = computed(() => this.estRestreint() || !!this.lieuCourant()?.vigilance);

  protected readonly avecCoordonnees = computed(() => {
    const l = this.lieuCourant();
    return !!l && l.latitude !== null && l.longitude !== null;
  });

  protected readonly avecNoteDpn = computed(() => !!this.lieuCourant()?.precisions.includes('Permis DPN'));

  protected readonly pourCarte = computed(() => {
    const l = this.lieuCourant();
    return l ? [l] : [];
  });

  protected readonly suggestions = computed(() => {
    const l = this.lieuCourant();
    return l ? suggestionsPour(l, valeurs(this.voisins)) : [];
  });

  constructor() {
    // Une suggestion se clique en bas de page : le nouveau lieu s'ouvre en haut
    effect(() => {
      this.id();
      window.scrollTo(0, 0);
    });
  }

  ngOnDestroy(): void {
    clearTimeout(this.minuteurPartage);
  }

  protected async partager(lieu: LieuDetente): Promise<void> {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: lieu.nom, url });
      } catch {
        // Partage annulé par la personne : rien à signaler
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      this.annoncer('Lien copié');
    } catch {
      this.annoncer('Copie impossible : copiez l’adresse de la page');
    }
  }

  private annoncer(message: string): void {
    this.messagePartage.set(message);
    clearTimeout(this.minuteurPartage);
    this.minuteurPartage = setTimeout(() => this.messagePartage.set(''), 3000);
  }
}
