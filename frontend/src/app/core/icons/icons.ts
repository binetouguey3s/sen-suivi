// Registre figé des icônes.
// Seul ce fichier importe depuis @lucide/angular : tout le reste de
// l'application passe par <ss-icon>, jamais par un import Lucide direct.
import {
  LucideArrowRight,
  LucideBookOpen,
  LucideChartLine,
  LucideCircleAlert,
  LucideEye,
  LucideEyeOff,
  LucideHouse,
  LucideMapPin,
  LucideMessageCircle,
  LucidePhone,
  LucideSettings,
} from '@lucide/angular';

export const ICONES = {
  oeil: LucideEye,
  'oeil-barre': LucideEyeOff,
  alerte: LucideCircleAlert,
  accueil: LucideHouse,
  journal: LucideChartLine,
  ressources: LucideBookOpen,
  lieux: LucideMapPin,
  parametres: LucideSettings,
  chat: LucideMessageCircle,
  fleche: LucideArrowRight,
  telephone: LucidePhone,
} as const;

export type NomIcone = keyof typeof ICONES;
