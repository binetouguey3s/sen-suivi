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
  return `https://www.google.com/maps/dir/?api=1&destination=${lieu.latitude},${lieu.longitude}`;
}
