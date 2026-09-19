// Décodage minimal d'un JWT (partie payload) : pas besoin d'une librairie
// entière pour lire des claims côté client, ils ne sont jamais vérifiés
// ici (seul le back-end fait foi), juste affichés.
export interface ClaimsJeton {
  user_id: number;
  type_compte: 'utilisateur' | 'professionnel' | 'administrateur';
  nom: string;
  prenom?: string;
  exp: number;
}

export function decoderJeton(jeton: string): ClaimsJeton | null {
  try {
    const [, payload] = jeton.split('.'); 
    const normalise = payload.replace(/-/g, '+').replace(/_/g, '/');
    const complete = normalise.padEnd(normalise.length + ((4 - (normalise.length % 4)) % 4), '=');
    return JSON.parse(atob(complete));
  } catch {
    return null;
  }
}
