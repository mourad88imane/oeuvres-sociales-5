# Guide de Déploiement

## Préparation

### 1. Certificats SSL
```bash
# Let's Encrypt (Certbot)
sudo apt install certbot
sudo certbot certonly --standalone -d oeuvres-sociales.dz

# Copier vers le dossier nginx/ssl
sudo cp /etc/letsencrypt/live/oeuvres-sociales.dz/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/oeuvres-sociales.dz/privkey.pem nginx/ssl/key.pem
```

### 2. Configuration variables d'environnement
```bash
cp backend/.env.example backend/.env.production
# Éditer backend/.env.production avec les valeurs de production
```

### 3. Secrets requis
```bash
# Générer SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Générer REDIS_PASSWORD
openssl rand -base64 32

# Générer DB_PASSWORD
openssl rand -base64 32
```

## Déploiement Initial

```bash
# 1. Cloner le dépôt
git clone git@github.com:org/oeuvres-sociales.git
cd oeuvres-sociales

# 2. Préparer l'environnement
cp backend/.env.example backend/.env.production
# Éditer les valeurs

# 3. Préparer les certificats SSL
mkdir -p nginx/ssl
# Copier les certificats Let's Encrypt

# 4. Lancer les services
docker compose -f docker-compose.prod.yml up -d

# 5. Appliquer les migrations
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput

# 6. Collecter les fichiers statiques
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput --clear

# 7. Créer le superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 8. Vérifier
./scripts/healthcheck.sh
```

## Mises à Jour

```bash
# Déploiement automatisé
./scripts/deploy.sh production

# OU manuellement :
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --remove-orphans
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput --clear
docker system prune -f
```

## Stratégie de Migration Zero-Downtime

Pour les changements cassants de schéma DB :

1. **Phase 1** — Ajouter les nouvelles colonnes (nullable / avec défaut)
2. **Phase 2** — Déployer le code qui utilise les nouvelles colonnes
3. **Phase 3** — Migrer les données (tâche Celery asynchrone)
4. **Phase 4** — Supprimer les anciennes colonnes

## Variables d'Environnement (Production)

Cf. `backend/.env.example` pour la liste complète. Valeurs critiques :

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django (32+ caractères) |
| `DB_PASSWORD` | Mot de passe PostgreSQL |
| `REDIS_PASSWORD` | Mot de passe Redis |
| `SENTRY_DSN` | DSN Sentry pour le monitoring |
| `ALLOWED_HOSTS` | Domaines autorisés |
| `CORS_ALLOWED_ORIGINS` | Origines CORS autorisées |
