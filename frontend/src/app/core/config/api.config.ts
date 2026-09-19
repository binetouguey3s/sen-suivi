// URL de base de l'API Django (.env API_BASE_URL). Angular ne lit pas les
// fichiers .env au runtime : cette valeur sera à brancher sur un vrai
// mécanisme de configuration par environnement quand plusieurs
// déploiements existeront (pas nécessaire tant qu'il n'y a que le poste
// de développement).
export const API_BASE_URL = 'http://localhost:8000/api';
