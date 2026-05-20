# Runbook d'Exploitation — Oeuvres Sociales

## Architecture

```
[Client HTTPS]
     │
[Nginx:443]  → Reverse proxy, SSL, rate limiting
     │
├── [Frontend React:80]  → SPA (build statique)
│
├── [Backend Django:8000]  → API REST (Gunicorn x4)
│    ├── Celery Worker → Tâches asynchrones
│    └── Celery Beat   → Tâches périodiques
│
├── [Redis:6379]  → Cache + Broker Celery
│
├── [PgBouncer:5432]  → Connection pool PostgreSQL
│
└── [PostgreSQL:5432]  → Base de données
```

## Commandes Essentielles

### Service
```bash
# Voir l'état des services
docker compose -f docker-compose.prod.yml ps

# Voir les logs en temps réel
docker compose -f docker-compose.prod.yml logs -f

# Logs d'un service spécifique
docker compose -f docker-compose.prod.yml logs -f backend

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart backend

# Redémarrer tous les services
docker compose -f docker-compose.prod.yml restart
```

### Déploiement
```bash
# Déploiement complet
./scripts/deploy.sh production

# Déploiement manuel (quick)
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput --clear
```

### Django
```bash
# Shell Django
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# Shell PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres psql -U oeuvres_user -d oeuvres_sociales

# Migrations
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput

# Backups
./scripts/backup.sh full

# Restauration
gunzip -c backups/db/oeuvres_db_20250101_120000.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U oeuvres_user -d oeuvres_sociales
```

## Procédures d'Urgence

### Incident: Application injoignable
```bash
# 1. Vérifier les services
docker compose -f docker-compose.prod.yml ps

# 2. Vérifier les logs
docker compose -f docker-compose.prod.yml logs --tail=50

# 3. Vérifier la base de données
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U oeuvres_user

# 4. Vérifier Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli -a "$REDIS_PASSWORD" ping

# 5. Redémarrer les services défaillants
docker compose -f docker-compose.prod.yml restart backend
```

### Incident: Erreurs 5xx
```bash
# 1. Voir les erreurs récentes dans Sentry
# 2. Vérifier les logs backend
docker compose -f docker-compose.prod.yml logs --tail=100 backend

# 3. Vérifier les connexions DB
docker compose -f docker-compose.prod.yml exec postgres psql -U oeuvres_user -d oeuvres_sociales -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Vérifier la charge CPU/MEM
docker stats --no-stream

# 5. Si surcharge : augmenter les replicas
docker compose -f docker-compose.prod.yml up -d --scale backend=4
```

### Incident: Espace disque saturé
```bash
# 1. Voir l'utilisation
df -h

# 2. Nettoyer les images/containers inutilisés
docker system prune -af --volumes

# 3. Vérifier les logs volumineux
du -sh /var/log/nginx/
du -sh backend/logs/

# 4. Nettoyer les backups anciens
find /opt/backups -name "*.sql.gz" -mtime +30 -delete
```

### Rollback
```bash
# 1. Déployer la version précédente
docker compose -f docker-compose.prod.yml down
# Remplacer IMAGE_TAG par le SHA précédent
export IMAGE_TAG=abc123def
docker compose -f docker-compose.prod.yml up -d

# 2. Si migration buggée, revenir en arrière
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate <app_name> <previous_migration>

# 3. Restaurer la DB depuis le dernier backup
gunzip -c backups/db/oeuvres_db_latest.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U oeuvres_user -d oeuvres_sociales
```

## Sauvegardes

### Configuration cron (daily à 2h du matin)
```cron
0 2 * * * /opt/oeuvres-sociales/scripts/backup.sh full >> /var/log/oeuvres-backup.log 2>&1
0 3 * * * /opt/oeuvres-sociales/scripts/rotate-logs.sh
```

### Rotation des backups
- DB : conservation 30 jours
- Fichiers : conservation 30 jours
- Configuration : conservation 90 jours
- Backup S3 : archive Glacier (coût réduit)

## Monitoring

### Alertes critiques
| Alerte | Seuil | Action |
|--------|-------|--------|
| Backend Down | Injoignable > 1m | Redémarrer le service |
| Celery Down | Injoignable > 2m | Vérifier Redis + Worker |
| DB Down | Injoignable > 30s | Vérifier PostgreSQL |
| Disque < 10% | Espace libre | Nettoyer + augmenter volume |
| Erreurs 5xx > 10 | /5 min | Vérifier logs + Sentry |

### Métriques clés
| Métrique | Cible | Warning | Critique |
|----------|-------|---------|----------|
| Latence API p95 | < 500ms | > 1s | > 2s |
| Erreurs 5xx | < 0.1% | > 1% | > 5% |
| Connexions DB | < 50 | > 100 | > 150 |
| File Celery | < 10 | > 50 | > 100 |
| CPU Backend | < 60% | > 80% | > 90% |
| Mémoire Backend | < 512MB | > 768MB | > 1GB |
