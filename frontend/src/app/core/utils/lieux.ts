import { imageDuLieu } from '../config/images-lieux';
import { LieuDetente } from '../models/suivi';

// Distance à vol d'oiseau en kilomètres (formule de haversine)
export function distanceKm(a: LieuDetente, b: LieuDetente): number {
  if (a.latitude === null || a.longitude === null || b.latitude === null || b.longitude === null) {
    return Number.POSITIVE_INFINITY;
  }
  const rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b.latitude - a.latitude);
  const dLon = rad(b.longitude - a.longitude);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a.latitude)) * Math.cos(rad(b.latitude)) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(h));
}

export function lienItineraire(lieu: LieuDetente): string {
  if (lieu.latitude !== null && lieu.longitude !== null) {
    return `https://www.google.com/maps/dir/?api=1&destination=${lieu.latitude},${lieu.longitude}`;
  }
  const recherche = encodeURIComponent(`${lieu.nom} ${lieu.ville} Sénégal`);
  return `https://www.google.com/maps/search/?api=1&query=${recherche}`;
}

// Montre le lieu dans Google Maps, sans calculer de trajet. Pour un lieu qui a des coordonnées
export function lienCarte(lieu: LieuDetente): string {
  return `https://www.google.com/maps/search/?api=1&query=${lieu.latitude},${lieu.longitude}`;
}

// Ce qu'on peut mettre en avant : jamais un lieu fermé ou sur autorisation
export function lieuxOuverts(lieux: LieuDetente[]): LieuDetente[] {
  return lieux.filter((l) => l.acces !== 'RESTREINT');
}

// Tri stable : les lieux avec une vraie photo d'abord, le reste dans le même ordre
export function avecPhotoDabord(lieux: LieuDetente[]): LieuDetente[] {
  return [...lieux].sort((a, b) => Number(imageDuLieu(b) !== null) - Number(imageDuLieu(a) !== null));
}

// Autres lieux de la même région à proposer : les plus proches d'abord, puis
// ceux de la même catégorie. Jamais un lieu fermé
export function suggestionsPour(courant: LieuDetente, lieux: LieuDetente[]): LieuDetente[] {
  const memeCategorie = (l: LieuDetente): number => Number(l.categorie !== courant.categorie);
  return lieuxOuverts(lieux)
    .filter((l) => l.id !== courant.id && l.region === courant.region)
    .sort((a, b) => {
      const da = distanceKm(courant, a);
      const db = distanceKm(courant, b);
      // Deux distances inconnues (Infinity) ne se soustraient pas : NaN fausserait le tri
      return da === db ? memeCategorie(a) - memeCategorie(b) : da < db ? -1 : 1;
    })
    .slice(0, 3);
}
