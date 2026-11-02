# 🚀 Guide d'Exécution - Sen Suivi

**Bienvenue ! Voici comment exécuter le projet sans modifier le code.**

---

## ✅ Prérequis (vérifiez que vous avez)

Avant de commencer, assurez-vous que **Docker** et **Docker Compose** sont installés :

```bash
docker --version
docker compose version
```

Si ce n'est pas le cas, installez [Docker Desktop](https://www.docker.com/products/docker-desktop) (il inclut Docker Compose).

---

## 🎯 Étape 1 : Préparer l'environnement (2 minutes)

À la racine du projet, créez le fichier `.env` à partir du modèle :

```bash
cp .env.example .env
```

**C'est tout !** Le fichier `.env` contient déjà toutes les configurations par défaut pour fonctionner.

---

## 🐳 Étape 2 : Lancer tous les services (3-5 minutes)

À la racine du projet, exécutez :

```bash
docker compose up --build
```

**Qu'est-ce qui se passe :**
- Docker va télécharger les images nécessaires
- Construire les conteneurs (backend, frontend, AI service)
- Lancer 5 services en parallèle

Attendez jusqu'à voir un message comme :
```
✓ Container sensuivi_db started
✓ Container sensuivi_backend started
✓ Container sensuivi_ai_service started
✓ Container sensuivi_frontend started
✓ Container sensuivi_n8n started
```

---

## 🗄️ Étape 3 : Initialiser la base de données (1 minute)

**Dans un NOUVEAU terminal** (sans arrêter le premier), exécutez :

```bash
docker compose exec backend python manage.py migrate
```

Attendez que la commande se termine.

---

## 📊 Étape 4 : Charger les données de démonstration (1 minute)

Toujours dans le même terminal :

```bash
docker compose exec backend python manage.py seed_donnees
```

**Important :** La commande va afficher un mot de passe pour tous les comptes de démonstration. **Notez-le** !

---

## 🔍 Étape 5 : Indexer les ressources pour le chatbot (1 minute)

```bash
docker compose exec backend python manage.py reindexer_ressources
```

---

## 🌐 Étape 6 : Accéder à l'application

Maintenant, ouvrez votre navigateur et visitez ces adresses :

### **Application principale** (ce que les utilisateurs voient)
```
http://localhost:4200
```

### **Administration Django** (gérer les données)
```
http://localhost:8000/admin/
```
- **Login :** Utilisez n'importe quel compte de démonstration (voir le mot de passe affiché à l'étape 4)

### **API Backend** (pour les développeurs)
```
http://localhost:8000/api/
```

### **API Chatbot (AI Service)**
```
http://localhost:8001/docs
```
Vous verrez la documentation interactive Swagger du chatbot.

### **Automatisations n8n**
```
http://localhost:5678
```

---

## 🧪 Test rapide du chatbot

1. Allez sur `http://localhost:4200`
2. Cliquez sur **"Chatbot"** ou trouvez la section chat
3. Envoyez un message comme :
   - `"Je me sens stressé"` → Le chatbot détectera le stress
   - `"Je suis en détresse"` → Ressources d'urgence
   - `"Comment méditer ?"` → Recherche dans les ressources

---

## 🛑 Arrêter l'application

Dans le terminal où vous avez lancé `docker compose up`, appuyez sur :
```
Ctrl + C
```

Pour arrêter et supprimer les conteneurs :
```bash
docker compose down
```

Pour arrêter ET supprimer les données (base de données, cache du chatbot) :
```bash
docker compose down -v
```

---

## 📱 Fonctionnalités à explorer

### **Visiteur (sans compte)**
- ✅ Accès au chatbot
- ✅ Consultation des ressources

### **Utilisateur connecté**
- 📔 Journal d'humeur (enregistrer son état de stress/anxiété)
- 📊 Tableau de bord (courbe sur 7 jours)
- 🔍 Auto-évaluation (score de tendance)
- 💬 Forum anonyme (participation à des discussions)
- 👨‍⚕️ Répertoire de professionnels validés
- 🚨 Ressources d'urgence (numéros Sénégal)

### **Administrateur**
- ✅ Validation des professionnels
- ✏️ Modération du forum
- 📚 Gestion des ressources

---

## 🐛 Dépannage

### **Les conteneurs ne se lancent pas**
```bash
docker compose logs
```
Regarde les erreurs. Souvent c'est un problème de port déjà utilisé.

### **Impossible de se connecter à la base de données**
```bash
docker compose restart db
```

### **Le frontend ne se lance pas**
```bash
docker compose logs frontend
```

### **Réinitialiser complètement**
```bash
docker compose down -v
docker system prune -a
docker compose up --build
```

---

## 📚 Structure des services

| Service | Port | URL | Rôle |
|---------|------|-----|------|
| **Frontend** | 4200 | http://localhost:4200 | Interface web Angular |
| **Backend** | 8000 | http://localhost:8000 | API REST Django |
| **AI Service** | 8001 | http://localhost:8001 | Chatbot FastAPI |
| **Base de données** | 5433 | localhost:5433 | PostgreSQL |
| **n8n** | 5678 | http://localhost:5678 | Automatisations |

---

## 💡 Conseils utiles

- 📋 **Tous les logs** : `docker compose logs -f` (affiche tous les services en direct)
- 📋 **Logs d'un service** : `docker compose logs -f backend` (ou `frontend`, `ai-service`, etc.)
- 🔧 **Vérifier les conteneurs actifs** : `docker compose ps`
- 🧹 **Nettoyer tout** : `docker compose down -v && docker system prune -a`

---

## ✨ Prêt ?

```bash
# 1. Créer le .env
cp .env.example .env

# 2. Lancer l'application
docker compose up --build

# 3. (Dans un autre terminal) Initialiser la BD
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_donnees
docker compose exec backend python manage.py reindexer_ressources

# 4. Ouvrir le navigateur
http://localhost:4200
```

**Bon test ! 🎉**
