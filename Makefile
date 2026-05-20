# ============================================================
# MAKEFILE — Commandes du projet Oeuvres Sociales
# Usage : make <commande>
# ============================================================

.PHONY: help dev stop restart logs shell test lint format migrate \
        createsuperuser collectstatic build clean seed

# ── Couleurs terminal ──────────────────────────────────────
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

# ── Configuration ─────────────────────────────────────────
COMPOSE = docker compose
BACKEND = $(COMPOSE) exec backend
FRONTEND = $(COMPOSE) exec frontend

# ── Aide ──────────────────────────────────────────────────
help: ## Affiche cette aide
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║     Oeuvres Sociales — Commandes Make            ║$(RESET)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Environnement ──────────────────────────────────────────
dev: ## Lance l'environnement de développement complet
	@echo "$(CYAN)🚀 Démarrage de l'environnement de développement...$(RESET)"
	@cp -n backend/.env.example backend/.env 2>/dev/null || true
	$(COMPOSE) up -d
	@echo "$(GREEN)✅ Environnement démarré$(RESET)"
	@echo ""
	@echo "  Frontend  : http://localhost:3000"
	@echo "  Backend   : http://localhost:8000"
	@echo "  API Docs  : http://localhost/api/docs/"
	@echo "  MailHog   : http://localhost:8025"
	@echo "  Admin     : http://localhost/admin/"
	@echo ""

stop: ## Arrête tous les services
	$(COMPOSE) down

restart: ## Redémarre tous les services
	$(COMPOSE) restart

restart-backend: ## Redémarre uniquement le backend
	$(COMPOSE) restart backend celery_worker celery_beat

logs: ## Affiche les logs (tous les services)
	$(COMPOSE) logs -f

logs-backend: ## Logs du backend Django
	$(COMPOSE) logs -f backend

logs-celery: ## Logs de Celery
	$(COMPOSE) logs -f celery_worker celery_beat

# ── Django ────────────────────────────────────────────────
shell: ## Shell Django interactif (shell_plus)
	$(BACKEND) python manage.py shell_plus

shell-simple: ## Shell Django simple (sans shell_plus)
	$(BACKEND) python manage.py shell

migrate: ## Applique les migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Crée les migrations
	$(BACKEND) python manage.py makemigrations

makemigrations-app: ## Crée les migrations pour une app spécifique : make makemigrations-app APP=users
	$(BACKEND) python manage.py makemigrations $(APP)

createsuperuser: ## Crée un superutilisateur
	$(BACKEND) python manage.py createsuperuser

collectstatic: ## Collecte les fichiers statiques
	$(BACKEND) python manage.py collectstatic --noinput

showmigrations: ## Affiche l'état des migrations
	$(BACKEND) python manage.py showmigrations

dbshell: ## Shell PostgreSQL
	$(COMPOSE) exec db psql -U oeuvres_user -d oeuvres_sociales_dev

# ── Tests ─────────────────────────────────────────────────
test: ## Lance tous les tests avec coverage
	$(BACKEND) pytest --cov=. --cov-report=term-missing --cov-report=html -v

test-fast: ## Tests rapides (sans coverage)
	$(BACKEND) pytest -x -v

test-app: ## Tests d'une app spécifique : make test-app APP=users
	$(BACKEND) pytest apps/$(APP)/ -v

test-watch: ## Tests en mode watch
	$(BACKEND) ptw -- -v

# ── Qualité code ──────────────────────────────────────────
lint: ## Vérifie le style du code (ruff)
	$(BACKEND) ruff check .
	$(COMPOSE) exec frontend npm run lint

format: ## Formate le code (black + isort)
	$(BACKEND) black .
	$(BACKEND) isort .
	$(COMPOSE) exec frontend npm run format

typecheck: ## Vérifie les types Python (mypy)
	$(BACKEND) mypy apps/ core/ shared/

# ── Build ─────────────────────────────────────────────────
build: ## Build les images Docker
	$(COMPOSE) build

build-backend: ## Build uniquement le backend
	$(COMPOSE) build backend celery_worker celery_beat

build-frontend: ## Build uniquement le frontend
	$(COMPOSE) build frontend

build-prod: ## Build en mode production
	$(COMPOSE) -f docker-compose.prod.yml build

# ── Base de données ───────────────────────────────────────
backup-db: ## Sauvegarde la base de données
	@mkdir -p backups
	$(COMPOSE) exec db pg_dump -U oeuvres_user oeuvres_sociales_dev > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup créé dans backups/$(RESET)"

restore-db: ## Restaure une sauvegarde : make restore-db FILE=backups/backup.sql
	$(COMPOSE) exec -T db psql -U oeuvres_user -d oeuvres_sociales_dev < $(FILE)

seed: ## Peuple la base avec des données de test
	$(BACKEND) python manage.py seed_data

reset-db: ## ⚠️  Réinitialise la base de données (DANGER)
	@echo "$(CYAN)⚠️  Cette commande va supprimer toutes les données !$(RESET)"
	@read -p "Confirmer ? (oui/non) : " confirm && [ "$$confirm" = "oui" ]
	$(COMPOSE) down -v
	$(COMPOSE) up -d db redis
	sleep 3
	$(BACKEND) python manage.py migrate
	@echo "$(GREEN)✅ Base de données réinitialisée$(RESET)"

# ── Frontend ──────────────────────────────────────────────
npm-install: ## Installe les dépendances npm
	$(COMPOSE) exec frontend npm install

npm-add: ## Ajoute un paquet npm : make npm-add PKG=axios
	$(COMPOSE) exec frontend npm install $(PKG)

# ── Nettoyage ─────────────────────────────────────────────
clean: ## Nettoie les fichiers temporaires
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name "htmlcov" -delete
	$(COMPOSE) exec frontend npm run clean 2>/dev/null || true

clean-docker: ## Supprime tous les containers et volumes (DANGER)
	$(COMPOSE) down -v --remove-orphans
	docker system prune -f

# ── Informations ──────────────────────────────────────────
status: ## Statut des services
	$(COMPOSE) ps

urls: ## Affiche toutes les URLs du projet
	$(BACKEND) python manage.py show_urls 2>/dev/null || $(BACKEND) python manage.py show_urls --format=table

version: ## Versions des outils
	@$(BACKEND) python --version
	@$(BACKEND) python -c "import django; print('Django', django.__version__)"
	@$(COMPOSE) exec frontend node --version
	@$(COMPOSE) exec frontend npm --version
