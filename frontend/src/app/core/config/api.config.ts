// URL de base de l'API Django. En production, la construction la remplace
// par la variable d'environnement API_BASE_URL (scripts/construire.mjs, option
// « define » d'Angular) ; sans elle, c'est l'API du poste de développement.
declare const SEN_SUIVI_API_BASE_URL: string | undefined;

export const API_BASE_URL =
  typeof SEN_SUIVI_API_BASE_URL === 'string' ? SEN_SUIVI_API_BASE_URL : 'http://localhost:8000/api';
