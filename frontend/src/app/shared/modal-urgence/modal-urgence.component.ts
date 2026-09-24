import { ChangeDetectionStrategy, Component, model } from '@angular/core';

import { IconComponent } from '../icon/icon.component';

interface ContactUrgence {
  libelle: string;
  valeur: string;
  telephone: string | null; // null : aucun numéro documenté, jamais inventé (docs/CONTEXTE.md section 1)
  misEnAvant?: boolean;
}

// docs/CONTEXTE.md section 1 : numéros du Sénégal uniquement, jamais 15, 112 ni un autre.
const CONTACTS_URGENCE: ContactUrgence[] = [
  {
    libelle: "Numéro vert d'écoute AJS",
    valeur: '800 805 805',
    telephone: '800805805',
    misEnAvant: true,
  },
  { libelle: 'SAMU', valeur: '1515', telephone: '1515' },
  { libelle: 'Sapeurs-pompiers', valeur: '18', telephone: '18' },
  { libelle: 'Service de psychiatrie', valeur: 'Hôpital de Fann, Dakar', telephone: '+221 33 869 18 43' },
];

@Component({
  selector: 'ss-modal-urgence',
  standalone: true,
  imports: [IconComponent],
  templateUrl: './modal-urgence.component.html',
  styleUrl: './modal-urgence.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalUrgenceComponent {
  readonly ouverte = model(false);
  protected readonly contacts = CONTACTS_URGENCE;

  protected fermer(): void {
    this.ouverte.set(false);
  }
}
