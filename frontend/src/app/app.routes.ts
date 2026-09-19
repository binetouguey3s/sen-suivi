import { Routes } from '@angular/router';

import { estConnecteGuard } from './core/guards/est-connecte.guard';

export const routes: Routes = [
  {
    path: 'connexion',
    loadComponent: () =>
      import('./features/auth/connexion/connexion.component').then((m) => m.ConnexionComponent),
  },
  {
    path: '',
    loadComponent: () =>
      import('./shared/layout-public/layout-public.component').then((m) => m.LayoutPublicComponent),
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/accueil/accueil.component').then((m) => m.AccueilComponent),
      },
      {
        path: 'ressources',
        loadComponent: () =>
          import('./features/ressources/bibliotheque.component').then((m) => m.BibliothequeComponent),
      },
      {
        path: 'ressources/:id',
        loadComponent: () =>
          import('./features/ressources/article.component').then((m) => m.ArticleComponent),
      },
    ],
  },
  {
    path: 'inscription',
    loadComponent: () =>
      import('./features/auth/inscription/inscription.component').then((m) => m.InscriptionComponent),
  },
  {
    path: 'inscription-professionnel',
    loadComponent: () =>
      import('./features/auth/inscription-pro/inscription-pro.component').then(
        (m) => m.InscriptionProComponent,
      ),
  },
  {
    path: 'mot-de-passe-oublie',
    loadComponent: () =>
      import('./features/auth/mot-de-passe-oublie/mot-de-passe-oublie.component').then(
        (m) => m.MotDePasseOublieComponent,
      ),
  },
  {
    path: 'nouveau-mot-de-passe',
    loadComponent: () =>
      import('./features/auth/nouveau-mot-de-passe/nouveau-mot-de-passe.component').then(
        (m) => m.NouveauMotDePasseComponent,
      ),
  },
  {
    path: 'bienvenue',
    canActivate: [estConnecteGuard],
    loadComponent: () =>
      import('./features/onboarding/onboarding.component').then((m) => m.OnboardingComponent),
  },
  {
    path: 'lieux',
    loadComponent: () =>
      import('./features/lieux/repertoire.component').then((m) => m.RepertoireComponent),
  },
  {
    path: 'lieux/:id',
    loadComponent: () => import('./features/lieux/lieu.component').then((m) => m.LieuComponent),
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
  { path: '**', redirectTo: '' },
];
