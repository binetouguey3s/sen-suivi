// Règle de robustesse du mot de passe, reprise du serveur (apps/comptes/validateurs.py).
// Le serveur reste la seule vérification qui fait foi : celle-ci guide seulement la saisie.

const SUITES_DE_REFERENCE = [
  'abcdefghijklmnopqrstuvwxyz',
  '0123456789',
  'azertyuiop',
  'qsdfghjklm',
  'wxcvbn',
  'qwertyuiop',
  'asdfghjkl',
  'zxcvbnm',
];
const LONGUEUR_SUITE = 5;

function contientSuite(texte: string): boolean {
  return SUITES_DE_REFERENCE.some((reference) =>
    [reference, [...reference].reverse().join('')].some((sens) => {
      for (let debut = 0; debut + LONGUEUR_SUITE <= sens.length; debut++) {
        if (texte.includes(sens.slice(debut, debut + LONGUEUR_SUITE))) return true;
      }
      return false;
    }),
  );
}

/** Message d'erreur à afficher, ou null si le mot de passe respecte la règle. */
export function verifierMotDePasse(motDePasse: string): string | null {
  if (motDePasse.length < 8) return 'Le mot de passe doit contenir au moins 8 caractères.';
  const categories = [/[A-Z]/, /[a-z]/, /\d/, /[^A-Za-z0-9]/].filter((motif) => motif.test(motDePasse)).length;
  if (categories < 3) {
    return 'Ajoutez au moins trois de ces éléments : une majuscule, une minuscule, un chiffre, un caractère spécial.';
  }
  const minuscule = motDePasse.toLowerCase();
  if (contientSuite(minuscule) || /(.)\1{3,}/.test(minuscule)) {
    return 'Évitez les suites évidentes (comme 12345 ou azerty) et les caractères répétés.';
  }
  return null;
}
