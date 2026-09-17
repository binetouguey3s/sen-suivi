# Sen Suivi — Explications de conception

Notes destinées à alimenter la partie Conception du mémoire. Rédigées pour être
comprises et défendues devant un jury.

---

## L'héritage de `CompteUtilisateur`

Dans le diagramme de classes, `CompteUtilisateur` est marqué `«abstract»` : c'est un concept qui n'existe jamais tout seul en réalité, seulement à travers `Utilisateur`, `Professionnel` ou `Administrateur`. En programmation orientée objet classique, une classe abstraite n'a pas d'instance directe, et le langage empêche même d'en créer.

Django doit gérer un contrainte que le diagramme ignore : le modèle qui sert à l'authentification (`AUTH_USER_MODEL`) doit correspondre à une vraie table en base, car tout le reste du projet (permissions, sessions, `ForeignKey` vers l'utilisateur connecté, etc.) a besoin de pointer vers une ligne concrète, avec un identifiant réel. Une classe purement abstraite en Django (au sens `abstract = True`) n'a justement pas de table : ses champs sont recopiés dans chaque sous-classe, sans lien entre elles. Impossible dans ce cas d'authentifier « un compte » de façon générique.

La solution retenue s'appelle l'**héritage multi-table**. Concrètement, cela crée :
- une table `comptes_compteutilisateur` avec les colonnes communes (`nom`, `email`, `password`, `date_creation`, etc.)
- une table `comptes_utilisateur` avec juste la colonne `prenom`, plus une colonne cachée `compteutilisateur_ptr_id` qui pointe vers la ligne correspondante dans la première table
- de la même façon, `comptes_professionnel` (avec `specialite`, `ville`...) et `comptes_administrateur`, chacune reliée par ce même genre de lien

Autrement dit : chaque `Utilisateur` a **deux lignes en base**, une dans la table commune et une dans sa table spécifique, connectées par une relation un-à-un automatique. Quand on demande `utilisateur.email`, Django va chercher dans la table commune sans que vous ayez à écrire de jointure ; c'est transparent.

C'est le seul choix viable ici parce que les deux autres options classiques ne fonctionnent pas :
- une vraie classe abstraite Django empêcherait d'avoir un `AUTH_USER_MODEL` unique connecté à l'authentification
- utiliser le modèle `User` natif de Django avec un « profil » séparé (un `Professionnel` relié par une simple `ForeignKey` à `User`) casserait la correspondance avec le diagramme : ce ne serait plus de l'héritage, mais une association, et on perdrait le lien conceptuel direct entre `CompteUtilisateur` et ses sous-types

## Pourquoi `Notification` peut, elle, rester abstraite

La différence tient à un seul critère : **est-ce que ce modèle doit être référencé génériquement ailleurs dans le projet ?**

`CompteUtilisateur` doit l'être : c'est la cible de `AUTH_USER_MODEL`, donc de toutes les connexions, de toutes les permissions, et de nombreuses `ForeignKey` dans d'autres apps (`SuiviHumeur.utilisateur`, `Notification.destinataire`, etc.). Il lui faut une table unique et interrogeable.

`Notification`, elle, n'est jamais pointée par personne : rien dans le projet n'a besoin de dire « voici une notification, peu importe si c'est un email ou un push ». On manipule toujours directement soit un `NotificationEmail`, soit un `NotificationPush`. Elle n'a donc pas besoin d'exister comme table à part entière.

En pratique, avec `abstract = True`, Django ne crée **aucune table `notifications_notification`**. Il recopie simplement les champs communs (`destinataire`, `contenu`, `date_envoi`, `statut`) dans les tables `notifications_notificationemail` et `notifications_notificationpush`, comme si vous les aviez écrits deux fois. C'est exactement ce que veut dire « abstrait » dans le diagramme : un patron de champs partagé, pas une entité qui existe par elle-même. Ici, contrairement à `CompteUtilisateur`, Django peut respecter le diagramme au pied de la lettre.

## Pourquoi les clés étrangères ciblent les sous-classes

Le diagramme dessine les associations directement depuis `Utilisateur` (pas depuis `CompteUtilisateur`) vers `SuiviHumeur`, `AutoEvaluation`, `DemandeContact`, etc. C'est une information métier précise : seul un `Utilisateur` tient un journal d'humeur ou envoie une demande de contact — pas un `Professionnel`, pas un `Administrateur`.

Si j'avais fait pointer ces clés étrangères vers `CompteUtilisateur` (la table commune), Django aurait accepté n'importe quel type de compte, sans distinction. **Exemple concret de ce que cela empêche** : avec une clé étrangère précise vers `comptes.Utilisateur`, il devient impossible en base de créer une `SuiviHumeur` liée à un `Professionnel` — la base de données refuserait l'enregistrement, car l'identifiant d'un professionnel n'existe pas dans la table `comptes_utilisateur`. C'est une garantie de cohérence imposée par la structure des données elle-même, avant même d'écrire la moindre ligne de code de validation dans l'API. Sans ce typage précis, il faudrait vérifier « à la main », dans chaque vue, qu'on n'a pas laissé un professionnel remplir un journal d'humeur — un oubli serait possible et silencieux.
