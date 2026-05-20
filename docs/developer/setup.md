# Guide du Développeur

## Stack Technique

- **Backend** : Python 3.12 / Django 5.1 / DRF 3.15
- **Frontend** : React 18 / TypeScript / Vite / Tailwind CSS
- **Base de données** : PostgreSQL 16 (+ PgBouncer)
- **Cache / Queue** : Redis 7
- **Tâches asynchrones** : Celery 5.4
- **Reverse Proxy** : Nginx
- **Monitoring** : Prometheus / Grafana / Sentry
- **CI/CD** : GitLab CI / GitHub Actions

## Prérequis

- Docker & Docker Compose v2
- Git
- Make (optionnel)

## Première Installation

```bash
# 1. Cloner le dépôt
git clone git@github.com:org/oeuvres-sociales.git
cd oeuvres-sociales

# 2. Copier le fichier d'environnement
cp backend/.env.example backend/.env

# 3. Lancer l'environnement de développement
make dev

# 4. Créer un superuser
make createsuperuser

# 5. (Optionnel) Charger des données de test
make seed
```

L'application est accessible sur :
- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Admin Django : http://localhost/admin/
- API Docs : http://localhost/api/docs/
- MailHog : http://localhost:8025

## Commandes Courantes

```bash
# Développement
make dev              # Lancer tous les services
make stop             # Arrêter tous les services
make logs             # Voir les logs
make shell            # Shell Django (shell_plus)

# Tests
make test             # Tests avec coverage
make test-fast        # Tests rapides
make test-app APP=users  # Tests d'une app

# Qualité
make lint             # Ruff + ESLint
make format           # Black + isort + Prettier
make typecheck        # mypy + tsc

# Base de données
make migrate          # Appliquer les migrations
make makemigrations   # Créer des migrations
make backup-db        # Sauvegarder la DB
make dbshell          # Shell PostgreSQL

# Frontend
make npm-add PKG=axios  # Ajouter un paquet npm
```

## Structure du Projet

```
oeuvres-sociales/
├── backend/
│   ├── apps/           # Applications Django métier
│   │   ├── authentication/
│   │   ├── users/
│   │   ├── employees/
│   │   ├── beneficiaries/
│   │   ├── benefits/
│   │   ├── finance/
│   │   ├── conventions/
│   │   ├── departments/
│   │   ├── reporting/
│   │   ├── dashboard/
│   │   └── monitoring/
│   ├── shared/         # Modules réutilisables
│   │   ├── ai/         # IA & Analytics
│   │   ├── audit/      # Piste d'audit
│   │   ├── api/        # Utilitaires API
│   │   ├── notifications/
│   │   ├── permissions/ # RBAC/ABAC
│   │   ├── registry/    # Plugin system
│   │   ├── reporting/   # Reporting engine
│   │   └── workflow/    # Workflow engine
│   ├── config/         # Configuration Django
│   ├── core/           # Fonctions transverses
│   ├── requirements/   # Dépendances
│   └── templates/      # Templates Django
├── frontend/
│   └── src/
│       ├── app/        # Configuration app
│       ├── modules/    # Modules fonctionnels
│       └── shared/     # Composants partagés
├── docker/             # Dockerfiles
├── nginx/              # Configuration Nginx
├── docs/               # Documentation
└── scripts/            # Scripts utilitaires
```

## Tests

```bash
# Backend
make test               # pytest avec coverage
make test-fast          # pytest sans coverage
make test-app APP=users # Tests d'une app spécifique

# Frontend
cd frontend && npm run test

# Exigences
- Tests unitaires : pytest + Factory Boy
- Coverage minimum : 80%
- Tests d'intégration pour les APIs
```
