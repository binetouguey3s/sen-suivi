import { Routes } from '@angular/router';

import { estConnecteGuard } from './core/guards/est-connecte.guard';
import { typeCompteGuard } from './core/guards/type-compte.guard';

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
        path: 'professionnels/:id',
        canActivate: [estConnecteGuard],
        loadComponent: () =>
          import('./features/professionnel/profil.component').then((m) => m.ProfilProfessionnelComponent),
      },
      {
        path: 'ressources/:id',
        loadComponent: () =>
          import('./features/ressources/article.component').then((m) => m.ArticleComponent),
      },
    ],
  },
  {
    path: 'pro',
    canActivate: [typeCompteGuard('professionnel')],
    loadComponent: () =>
      import('./shared/layout-app/layout-app.component').then((m) => m.LayoutAppComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/pro/tableau-de-bord-pro.component').then((m) => m.TableauDeBordProComponent),
      },
      {
        path: 'parametres',
        loadComponent: () =>
          import('./features/parametres/parametres.component').then((m) => m.ParametresComponent),
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
    canActivate: [typeCompteGuard('utilisateur')],
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
        path: 'statistiques',
        loadComponent: () =>
          import('./features/statistiques/statistiques.component').then((m) => m.StatistiquesComponent),
      },
      {
        path: 'parametres',
        loadComponent: () =>
          import('./features/parametres/parametres.component').then((m) => m.ParametresComponent),
      },
      {
        path: 'journal',
        loadComponent: () =>
          import('./features/journal/journal.component').then((m) => m.JournalComponent),
      },
    ],
  },
  {
    // Toute adresse inconnue : page 404 dans le layout public (doit rester la dernière route)
    path: '**',
    loadComponent: () =>
      import('./shared/layout-public/layout-public.component').then((m) => m.LayoutPublicComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/erreur/page-404.component').then((m) => m.Page404Component),
      },
    ],
  },
];
