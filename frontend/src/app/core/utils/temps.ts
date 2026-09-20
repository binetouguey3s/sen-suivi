// Formatage relatif d'une date ISO ("il y a 2 heures"), utilisé partout où
// l'API renvoie un horodatage (demandes de mise en relation, forum…).
export function depuisMaintenant(iso: string): string {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 60) return `il y a ${Math.max(minutes, 1)} min`;
  const heures = Math.round(minutes / 60);
  if (heures < 24) return `il y a ${heures} heures`;
  const jours = Math.round(heures / 24);
  return jours === 1 ? 'hier' : `il y a ${jours} jours`;
}
