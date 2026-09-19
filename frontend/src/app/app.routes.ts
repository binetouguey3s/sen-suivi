import { Routes } from '@angular/router';

import { estConnecteGuard } from './core/guards/est-connecte.guard';

export const routes: Routes = [
  {
    path: 'connexion',
    loadComponent: () =>
      import('./features/auth/connexion/connexion.component').then((m) => m.ConnexionComponent),
  },
  {
    path: 'app/evaluation/:type',
    canActivate: [estConnecteGuard],
    loadComponent: () =>
      import('./features/auto-evaluation/question/question.component').then(
        (m) => m.QuestionComponent,
      ),
  },
  {
    path: 'app/evaluation/:type/resultat',
    canActivate: [estConnecteGuard],
    loadComponent: () =>
      import('./features/auto-evaluation/resultat/resultat.component').then(
        (m) => m.ResultatComponent,
      ),
  },
  {
    path: 'app',
    canActivate: [estConnecteGuard],
    loadComponent: () =>
      import('./shared/layout-app/layout-app.component').then((m) => m.LayoutAppComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/tableau-de-bord/tableau-de-bord.component').then(
            (m) => m.TableauDeBordComponent,
          ),
      },
      {
        path: 'journal',
        loadComponent: () =>
          import('./features/journal/journal.component').then((m) => m.JournalComponent),
      },
    ],
  },
  { path: '', redirectTo: 'connexion', pathMatch: 'full' },
  { path: '**', redirectTo: 'connexion' },
];
