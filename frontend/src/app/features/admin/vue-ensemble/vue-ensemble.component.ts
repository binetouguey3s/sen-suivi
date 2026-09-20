import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { API_BASE_URL } from '../../../core/config/api.config';
import { VueEnsembleAdmin } from '../../../core/models/administration';
import { IconComponent } from '../../../shared/icon/icon.component';

@Component({
  selector: 'ss-admin-vue-ensemble',
  standalone: true,
  imports: [RouterLink, IconComponent],
  templateUrl: './vue-ensemble.component.html',
  styleUrl: './vue-ensemble.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminVueEnsembleComponent {
  protected readonly vue = httpResource<VueEnsembleAdmin>(() => `${API_BASE_URL}/administration/vue-ensemble`);
}
