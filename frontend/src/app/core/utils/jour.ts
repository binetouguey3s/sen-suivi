// Jour de l'année (1 à 366), en heure locale : sert à tout ce qui doit rester
// le même toute la journée et changer le lendemain (conseil, phrases du journal).
export function jourDeLAnnee(date: Date): number {
  const debut = new Date(date.getFullYear(), 0, 0);
  const aujourdHui = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  return Math.round((aujourdHui.getTime() - debut.getTime()) / 86_400_000);
}
