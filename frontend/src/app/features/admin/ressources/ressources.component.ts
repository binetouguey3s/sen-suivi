import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';

import { API_BASE_URL } from '../../../core/config/api.config';
import { RessourceAdmin } from '../../../core/models/administration';
import { AdministrationService } from '../../../core/services/administration.service';
import { ICONE_PAR_TYPE, LIBELLE_PAR_TYPE } from '../../../core/utils/ressources';
import { valeurs } from '../../../core/utils/ressource';
import { ChampComponent } from '../../../shared/champ/champ.component';
import { IconComponent } from '../../../shared/icon/icon.component';
import { ModalComponent } from '../../../shared/modal/modal.component';

type Format = RessourceAdmin['type_ressource'];
const FORMATS: Format[] = ['ARTICLE', 'EXERCICE', 'PODCAST'];

@Component({
  selector: 'ss-admin-ressources',
  standalone: true,
  imports: [ChampComponent, IconComponent, ModalComponent],
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

  protected readonly ressources = httpResource<RessourceAdmin[]>(() => `${API_BASE_URL}/ressources`, {
    defaultValue: [],
  });
  protected readonly liste = () => valeurs(this.ressources);

  protected readonly modaleOuverte = signal(false);
  protected readonly enEdition = signal<RessourceAdmin | null>(null);
  protected readonly titre = signal('');
  protected readonly formatChoisi = signal<Format>('ARTICLE');
  protected readonly thematique = signal('');
  protected readonly dureeLecture = signal(5);
  protected readonly contenu = signal('');
  protected readonly envoiEnCours = signal(false);
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
    this.erreur.set(null);
    this.modaleOuverte.set(true);
  }

  protected ouvrirEdition(ressource: RessourceAdmin): void {
    this.enEdition.set(ressource);
    this.titre.set(ressource.titre);
    this.formatChoisi.set(ressource.type_ressource);
    this.thematique.set(ressource.thematique);
    this.dureeLecture.set(ressource.duree_lecture);
    this.contenu.set(ressource.contenu);
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
    this.envoiEnCours.set(true);
    this.erreur.set(null);
    const donnees = {
      titre: this.titre().trim(),
      type_ressource: this.formatChoisi(),
      thematique: this.thematique().trim(),
      duree_lecture: this.dureeLecture(),
      contenu: this.contenu().trim(),
    };
    try {
      const existante = this.enEdition();
      if (existante) {
        await this.administration.modifierRessource(existante.id, donnees);
      } else {
        await this.administration.creerRessource(donnees);
      }
      this.modaleOuverte.set(false);
      this.ressources.reload();
    } catch {
      this.erreur.set("L'enregistrement a échoué. Réessayez dans un instant.");
    } finally {
      this.envoiEnCours.set(false);
    }
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
