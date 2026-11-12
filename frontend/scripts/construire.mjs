// Construction de production (Vercel) : la variable d'environnement
// API_BASE_URL devient l'adresse de l'API dans le code construit.
// Usage : API_BASE_URL=https://sen-suivi-api.onrender.com/api node scripts/construire.mjs
import { spawnSync } from 'node:child_process';

const api = (process.env.API_BASE_URL ?? '').trim().replace(/\/+$/, '');
if (!/^https?:\/\/.+\/api$/.test(api)) {
  console.error(`API_BASE_URL doit être l'adresse complète de l'API et finir par /api (reçu : « ${api} »).`);
  process.exit(1);
}

const resultat = spawnSync(
  'npx',
  ['ng', 'build', '--configuration', 'production', '--define', `SEN_SUIVI_API_BASE_URL=${JSON.stringify(api)}`],
  { stdio: 'inherit' },
);
process.exit(resultat.status ?? 1);
