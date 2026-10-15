import { HttpClient, HttpEventType } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { filter, firstValueFrom, lastValueFrom, tap } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { Ressource } from '../models/suivi';

// Ce que le professionnel saisit dans l'éditeur (le statut ne se choisit jamais)
export type BrouillonRessource = Pick<Ressource, 'titre' | 'type_ressource' | 'thematique' | 'contenu' | 'duree_lecture'> & {
  url_video?: string;
};

// Ressources proposées par le professionnel connecté (/api/pro/ressources) :
// brouillons, soumission à l'équipe, fichier audio d'un podcast.
@Injectable({ providedIn: 'root' })
export class RessourcesProService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/pro/ressources`;

  // Incrémenté à chaque changement : la liste et le compteur de la navigation se rechargent
  readonly version = signal(0);
  // Message affiché en haut de la liste après une soumission réussie
  readonly soumissionReussie = signal(false);

  private changement(): void {
    this.version.update((v) => v + 1);
  }

  async creer(donnees: BrouillonRessource): Promise<Ressource> {
    const ressource = await firstValueFrom(this.http.post<Ressource>(this.url, donnees));
    this.changement();
    return ressource;
  }

  async modifier(id: number, donnees: Partial<BrouillonRessource>): Promise<Ressource> {
    const ressource = await firstValueFrom(this.http.patch<Ressource>(`${this.url}/${id}`, donnees));
    this.changement();
    return ressource;
  }

  async supprimer(id: number): Promise<void> {
    await firstValueFrom(this.http.delete(`${this.url}/${id}`));
    this.changement();
  }

  async soumettre(id: number): Promise<Ressource> {
    const ressource = await firstValueFrom(
      this.http.post<Ressource>(`${this.url}/${id}/soumettre`, { charte_acceptee: true }),
    );
    this.soumissionReussie.set(true);
    this.changement();
    return ressource;
  }

  // Fichier audio d'un podcast (multipart), avec la progression en pourcentage
  async envoyerAudio(id: number, fichier: File, progression: (pourcentage: number) => void): Promise<Ressource> {
    const corps = new FormData();
    corps.append('fichier_audio', fichier);
    const reponse = await lastValueFrom(
      this.http.patch<Ressource>(`${this.url}/${id}`, corps, { reportProgress: true, observe: 'events' }).pipe(
        tap((evenement) => {
          if (evenement.type === HttpEventType.UploadProgress && evenement.total) {
            progression(Math.round((evenement.loaded / evenement.total) * 100));
          }
        }),
        filter((evenement) => evenement.type === HttpEventType.Response),
      ),
    );
    this.changement();
    return reponse.body!;
  }
}
