# Plateforme de Gestion des Oeuvres Sociales

Plateforme modulaire de gestion des oeuvres sociales, construite avec Django REST Framework et React + Vite.

## Stack Technique

| Couche      | Technologie                              |
|-------------|------------------------------------------|
| Backend     | Django 5.1 + DRF + SimpleJWT            |
| Frontend    | React 18 + Vite + TypeScript + Tailwind |
| Base de données | PostgreSQL 16                       |
| Cache/Queue | Redis 7 + Celery                        |
| Proxy       | Nginx                                   |
| Infra       | Docker + Docker Compose                 |

## Démarrage rapide

### Prérequis
- Docker Desktop ≥ 4.x
- Make (inclus sur Linux/macOS, `choco install make` sur Windows)

### Lancer l'environnement de développement

```bash
# 1. Cloner le projet
git clone <repo> oeuvres-sociales
cd oeuvres-sociales

# 2. Lancer tout l'environnement (DB, backend, frontend, nginx...)
make dev

# 3. Créer le super utilisateur admin
make createsuperuser
```

### URLs de développement

| Service       | URL                              |
|---------------|----------------------------------|
| Application   | http://localhost                 |
| API Docs      | http://localhost/api/docs/       |
| Admin Django  | http://localhost/admin/          |
| MailHog       | http://localhost:8025            |
| Backend direct| http://localhost:8000            |
| Frontend direct| http://localhost:3000           |

## Commandes principales

```bash
make help           # Aide complète
make dev            # Démarrer l'environnement
make stop           # Arrêter l'environnement
make test           # Lancer les tests
make lint           # Vérifier le code
make migrate        # Appliquer les migrations
make shell          # Shell Django interactif
make logs           # Voir les logs
make backup-db      # Sauvegarder la base de données
```

## Architecture des modules

```
backend/
├── apps/
│   ├── authentication/     # JWT, login, logout
│   ├── users/              # Utilisateurs, rôles (admin/gestionnaire/comptable/consultant)
│   ├── employees/          # Dossiers employés
│   ├── beneficiaries/      # Ayants droit
│   ├── benefits/           # Prestations (workflow: brouillon→soumise→validée→payée)
│   ├── finance/            # Paiements, budgets
│   ├── conventions/        # Partenaires conventionnés
│   ├── reporting/          # Rapports
│   └── dashboard/          # KPIs et analytics
├── core/                   # BaseModel, permissions, pagination, exceptions
└── shared/
    ├── audit/              # Journal d'audit (préparation AI)
    ├── workflow/           # Moteur de workflow réutilisable
    └── notifications/      # Service de notifications

frontend/src/
├── modules/               # Miroir des apps Django
│   ├── auth/              # Login, logout, store JWT
│   ├── dashboard/         # Tableau de bord
│   ├── employees/         # Liste employés
│   ├── benefits/          # Prestations + workflow UI
│   └── users/             # Gestion utilisateurs
└── shared/
    ├── api/               # Axios client avec refresh JWT auto
    ├── components/
    │   ├── layout/        # AppLayout, Sidebar, ProtectedRoute
    │   └── ui/            # Composants réutilisables
    └── hooks/             # Hooks partagés
```

## Workflow des prestations

```
Brouillon → Soumise → Validée → Payée
                ↓          ↓
             Rejetée    Rejetée
```

## Rôles et permissions

| Rôle         | Employés | Prestations     | Finance | Admin |
|--------------|----------|-----------------|---------|-------|
| Admin        | CRUD     | CRUD + Workflow  | CRUD    | ✅    |
| Gestionnaire | CRUD     | Créer/Valider   | Lecture | ❌    |
| Comptable    | Lecture  | Voir/Payer      | CRUD    | ❌    |
| Consultant   | Lecture  | Lecture         | ❌      | ❌    |

## Variables d'environnement

Copier `backend/.env.example` en `backend/.env` et ajuster les valeurs.
Copier `frontend/.env.example` en `frontend/.env.local`.

**Ne jamais committer les fichiers `.env`.**

## Tests

```bash
make test           # Tous les tests avec coverage
make test-fast      # Tests rapides sans coverage
make test-app APP=users  # Tests d'un module
```

Couverture minimum exigée : **80%**

## Roadmap

- **Phase 1** (mois 1-3) : Fondations + Auth + Employés ✅
- **Phase 2** (mois 4-6) : Prestations + Finance + Conventions
- **Phase 3** (mois 7-9) : Reporting + Dashboard avancé
- **Phase 4** (mois 10-11) : Sécurité + Tests E2E + Audit
- **Phase 5** (mois 12+) : AI + Analytics + Recommandations
