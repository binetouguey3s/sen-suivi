// « Conseil du jour » du tableau de bord : une astuce bien-être courte, non
// clinique, sans promesse. Le conseil change chaque jour et reste le même
// toute la journée. Avec le consentement et un onboarding, les conseils qui
// répondent aux préoccupations de la personne passent en premier.

import { ProfilOnboarding } from '../../core/models/onboarding';
import { jourDeLAnnee } from '../../core/utils/jour';
import { THEMATIQUES_PAR_PREOCCUPATION } from '../../core/utils/suggestions';

export interface Conseil {
  texte: string;
  thematique: string;
}

export const CONSEILS: readonly Conseil[] = [
  { thematique: 'Stress', texte: 'Le soir, une marche de vingt minutes sur la Corniche, face à la mer, aide à poser la journée. Laissez le téléphone dans la poche.' },
  { thematique: 'Respiration', texte: 'Avant un examen ou une réunion, inspirez sur quatre temps et expirez sur six, cinq fois de suite. L’expiration plus longue calme le corps.' },
  { thematique: 'Lien social', texte: 'Proposez un ataya à un ami cette semaine. Les trois verres laissent le temps de parler vraiment.' },
  { thematique: 'Numérique', texte: 'Coupez les notifications WhatsApp pendant une heure aujourd’hui. Les messages vous attendront, votre attention vous reviendra.' },
  { thematique: 'Bien-être', texte: 'Avec la chaleur, gardez une bouteille d’eau à portée de main et buvez par petites gorgées, même sans soif.' },
  { thematique: 'Sommeil', texte: 'Posez votre téléphone hors de la chambre trente minutes avant de dormir. Le sommeil vient plus facilement sans écran.' },
  { thematique: 'Motivation', texte: 'Choisissez une seule petite chose à terminer aujourd’hui, et notez-la. La cocher fait du bien.' },
  { thematique: 'Études', texte: 'Révisez par blocs de vingt-cinq minutes, puis faites cinq minutes de pause loin des cahiers. Le cerveau retient mieux.' },
  { thematique: 'Travail', texte: 'Entre deux tâches, levez-vous et étirez les bras pendant une minute. Le corps aussi a besoin d’une pause.' },
  { thematique: 'Émotions', texte: 'Quand une émotion est forte, nommez-la à voix basse : « je suis en colère », « je suis triste ». La nommer aide à prendre du recul.' },
  { thematique: 'Famille', texte: 'Partagez un repas sans téléphone avec votre famille cette semaine. Autour du bol, les conversations reviennent d’elles-mêmes.' },
  { thematique: 'Organisation', texte: 'Le dimanche soir, écrivez les trois choses importantes de la semaine. Le reste peut attendre ou être confié.' },
  { thematique: 'Confiance en soi', texte: 'Ce soir, notez une chose que vous avez bien faite aujourd’hui, même petite. Elle compte.' },
  { thematique: 'Lien social', texte: 'Appelez un proche que vous n’avez pas entendu depuis longtemps, juste pour prendre des nouvelles.' },
  { thematique: 'Stress', texte: 'Quand tout s’accélère, posez les pieds bien à plat, relâchez les épaules et comptez dix respirations lentes.' },
  { thematique: 'Sommeil', texte: 'Essayez de vous coucher et de vous lever à la même heure, même le week-end. Le corps aime la régularité.' },
  { thematique: 'Numérique', texte: 'Le matin, attendez d’avoir pris votre petit-déjeuner avant d’ouvrir les réseaux sociaux. La journée commence par vous.' },
  { thematique: 'Bien-être', texte: 'Profitez de la fraîcheur du matin ou de la fin d’après-midi pour bouger un peu : marcher, danser, jouer avec les enfants.' },
  { thematique: 'Motivation', texte: 'Pensez à la raison qui vous a fait commencer ce projet. L’écrire en une phrase redonne de l’élan.' },
  { thematique: 'Études', texte: 'Expliquez une leçon à voix haute, comme à un camarade. Ce que l’on sait expliquer, on le retient.' },
  { thematique: 'Expression', texte: 'Écrivez trois lignes dans votre journal ce soir, sans vous relire. Ce qui est posé sur le papier pèse moins dans la tête.' },
  { thematique: 'Relations', texte: 'Dans une discussion difficile, parlez de ce que vous ressentez (« je me sens… ») plutôt que de faire un reproche. L’échange reste plus doux.' },
  { thematique: 'Respiration', texte: 'Dans un car rapide ou un embouteillage, profitez de l’attente pour respirer lentement par le nez. Le temps passe autrement.' },
  { thematique: 'Travail', texte: 'Fixez-vous une heure de fin de travail et respectez-la ce soir. Le repos fait partie du travail bien fait.' },
  { thematique: 'Émotions', texte: 'Écoutez un morceau qui vous fait du bien, les yeux fermés, sans rien faire d’autre. Trois minutes pour vous.' },
  { thematique: 'Deuil', texte: 'Le chagrin n’a pas de calendrier. Accordez-vous un moment pour penser à la personne disparue, seul·e ou avec un proche.' },
  { thematique: 'Organisation', texte: 'Découpez la tâche qui vous fait peur en petites étapes, et ne regardez que la première.' },
  { thematique: 'Confiance en soi', texte: 'Acceptez un compliment aujourd’hui avec un simple « merci », sans le minimiser.' },
  { thematique: 'Bien-être', texte: 'Asseyez-vous quelques minutes à l’ombre d’un arbre ou près d’une fenêtre, et observez simplement ce qui vous entoure.' },
  { thematique: 'Lien social', texte: 'Si vous vous sentez seul·e, le forum de Sen Suivi permet d’échanger avec d’autres personnes, sous un pseudonyme.' },
];

// Thématiques des préoccupations, seulement avec le consentement
function thematiquesPreferees(profil: ProfilOnboarding | undefined, consentement: boolean): Set<string> {
  if (!consentement || !profil) return new Set();
  return new Set((profil.preoccupations ?? []).flatMap((p) => THEMATIQUES_PAR_PREOCCUPATION[p] ?? []));
}

// `decalage` : nombre de clics sur « Un autre conseil ». Ordre de lecture : les
// conseils qui répondent aux préoccupations d'abord, puis les autres. Le conseil
// du jour tourne parmi les prioritaires s'il y en a, sinon parmi tous.
export function conseilDuJour(
  date: Date,
  profil: ProfilOnboarding | undefined,
  consentement: boolean,
  decalage = 0,
): Conseil {
  const preferees = thematiquesPreferees(profil, consentement);
  const prioritaires = CONSEILS.filter((c) => preferees.has(c.thematique));
  const liste = [...prioritaires, ...CONSEILS.filter((c) => !preferees.has(c.thematique))];
  const depart = jourDeLAnnee(date) % (prioritaires.length || liste.length);
  return liste[(depart + decalage) % liste.length];
}
