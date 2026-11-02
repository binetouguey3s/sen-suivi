import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, input, signal } from '@angular/core';
import { ActivatedRoute, Params, Router, RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../core/config/api.config';
import { ACCES, ACCES_PAR_CODE, CATEGORIES, MENTION_TARIFS, REGIONS } from '../../core/config/lieux';
import { AccesLieu, LieuDetente } from '../../core/models/suivi';
import { AuthService } from '../../core/services/auth.service';
import { CarteLieuComponent } from '../../shared/carte-lieu/carte-lieu.component';
import { CarteLieuxComponent } from '../../shared/carte-lieux/carte-lieux.component';
import { IconComponent } from '../../shared/icon/icon.component';
import { avecPhotoDabord } from '../../core/utils/lieux';
import { valeurs } from '../../core/utils/ressource';

function pluriel(nombre: number, singulier: string, plurielForme: string): string {
  return `${nombre} ${nombre > 1 ? plurielForme : singulier}`;
}

@Component({
  selector: 'ss-repertoire-lieux',
  standalone: true,
  imports: [RouterLink, IconComponent, CarteLieuxComponent, CarteLieuComponent],
  templateUrl: './repertoire.component.html',
  styleUrl: './repertoire.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RepertoireComponent {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  protected readonly auth = inject(AuthService);

  // Paramètres d'URL liés aux entrées : l'adresse est la seule source des
  // filtres, une recherche se partage donc telle quelle
  readonly region = input<string>();
  readonly categorie = input<string>();
  readonly acces = input<string | string[]>();
  readonly q = input<string>();
  readonly ouverts = input<string>();

  protected readonly categories = CATEGORIES;
  protected readonly optionsAcces = ACCES;
  protected readonly mentionTarifs = MENTION_TARIFS;
  protected readonly squelettes = [1, 2, 3, 4];

  protected readonly selection = signal<number | null>(null);
  protected readonly carteVisibleMobile = signal(false);
  protected readonly filtresOuverts = signal(false);

  private minuteur: ReturnType<typeof setTimeout> | undefined;

  protected readonly accesChoisis = computed<AccesLieu[]>(() => {
    const valeur = this.acces();
    const liste = valeur === undefined ? [] : Array.isArray(valeur) ? valeur : [valeur];
    return liste.filter((a): a is AccesLieu => ACCES_PAR_CODE.has(a as AccesLieu));
  });

  // Choisir « Restreint » revient à vouloir voir les lieux fermés
  protected readonly masquerFermes = computed(
    () => this.ouverts() !== '0' && !this.accesChoisis().includes('RESTREINT'),
  );

  // Tous les lieux : sert uniquement au nombre de lieux par région
  private readonly tous = httpResource<LieuDetente[]>(() => `${API_BASE_URL}/lieux`, { defaultValue: [] });

  // Filtres appliqués côté serveur. Le masquage se fait ici, sur la réponse,
  // pour pouvoir dire combien de lieux fermés correspondent à la recherche
  protected readonly lieux = httpResource<LieuDetente[]>(
    () => {
      const params = new URLSearchParams();
      const region = this.region();
      const categorie = this.categorie();
      const q = this.q()?.trim();
      if (region) params.set('region', region);
      if (categorie) params.set('categorie', categorie);
      for (const code of this.accesChoisis()) params.append('acces', code);
      if (q) params.set('q', q);
      const chaine = params.toString();
      return `${API_BASE_URL}/lieux${chaine ? `?${chaine}` : ''}`;
    },
    { defaultValue: [] },
  );

  private readonly apresMasque = (liste: LieuDetente[]): LieuDetente[] =>
    this.masquerFermes() ? liste.filter((l) => l.acces !== 'RESTREINT') : liste;

  protected readonly visibles = computed(() => avecPhotoDabord(this.apresMasque(valeurs(this.lieux))));
  protected readonly nombreMasques = computed(() => valeurs(this.lieux).length - this.visibles().length);
  protected readonly messageMasques = computed(() => {
    const n = this.nombreMasques();
    return n > 1 ? `${n} lieux fermés masqués` : `${n} lieu fermé masqué`;
  });

  protected readonly boutonResultats = computed(() => {
    const n = this.visibles().length;
    return n > 1 ? `Voir les ${n} lieux` : n === 1 ? 'Voir le lieu' : 'Aucun lieu pour ces filtres';
  });

  protected readonly optionsRegion = computed(() => {
    const ouverts = this.apresMasque(valeurs(this.tous));
    return {
      total: ouverts.length,
      regions: REGIONS.map((nom) => ({ nom, nombre: ouverts.filter((l) => l.region === nom).length })),
    };
  });

  protected readonly nombreFiltres = computed(
    () => (this.region() ? 1 : 0) + (this.categorie() ? 1 : 0) + this.accesChoisis().length,
  );

  protected readonly ligneResultats = computed(() =>
    [pluriel(this.visibles().length, 'lieu trouvé', 'lieux trouvés'), this.region(), this.categorie()]
      .filter(Boolean)
      .join(' · '),
  );

  protected readonly filtresActifs = computed(() => {
    const actifs: { libelle: string; retirer: () => void }[] = [];
    const region = this.region();
    const categorie = this.categorie();
    const q = this.q();
    if (q) actifs.push({ libelle: `« ${q} »`, retirer: () => this.naviguer({ q: null }) });
    if (region) actifs.push({ libelle: region, retirer: () => this.naviguer({ region: null }) });
    if (categorie) actifs.push({ libelle: categorie, retirer: () => this.naviguer({ categorie: null }) });
    for (const code of this.accesChoisis()) {
      actifs.push({ libelle: ACCES_PAR_CODE.get(code)!.libelle, retirer: () => this.basculerAcces(code) });
    }
    return actifs;
  });

  protected readonly messageCarte = computed(() => {
    const n = this.visibles().filter((l) => l.latitude !== null && l.longitude !== null).length;
    return `${pluriel(n, 'lieu affiché', 'lieux affichés')} sur la carte`;
  });

  private naviguer(queryParams: Params): void {
    this.selection.set(null);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams,
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  protected saisirRecherche(evenement: Event): void {
    const valeur = (evenement.target as HTMLInputElement).value;
    clearTimeout(this.minuteur);
    this.minuteur = setTimeout(() => this.naviguer({ q: valeur.trim() || null }), 250);
  }

  protected choisirRegion(evenement: Event): void {
    this.naviguer({ region: (evenement.target as HTMLSelectElement).value || null });
  }

  protected basculerCategorie(nom: string): void {
    this.naviguer({ categorie: this.categorie() === nom ? null : nom });
  }

  protected basculerAcces(code: AccesLieu): void {
    const choisis = this.accesChoisis();
    const actif = choisis.includes(code);
    const acces = actif ? choisis.filter((a) => a !== code) : [...choisis, code];
    const changement: Params = { acces: acces.length ? acces : null };
    // Retirer « Restreint » redonne le masquage par défaut
    if (code === 'RESTREINT') changement['ouverts'] = actif ? null : '0';
    this.naviguer(changement);
  }

  protected basculerMasque(evenement: Event): void {
    if ((evenement.target as HTMLInputElement).checked) {
      const acces = this.accesChoisis().filter((a) => a !== 'RESTREINT');
      this.naviguer({ ouverts: null, acces: acces.length ? acces : null });
    } else {
      this.naviguer({ ouverts: '0' });
    }
  }

  protected afficherFermes(): void {
    this.naviguer({ ouverts: '0' });
  }

  protected toutEffacer(): void {
    clearTimeout(this.minuteur);
    this.selection.set(null);
    void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
  }

  protected ouvrir(id: number): void {
    void this.router.navigate(['/lieux', id]);
  }
}
