# Checklist Déploiement Production

## Pré-requis
- [ ] Nom de domaine configuré (A record → IP serveur)
- [ ] Certificats SSL (Let's Encrypt / cert-manager)
- [ ] Comptes de service créés (Docker registry, Sentry, AWS S3)
- [ ] Accès SSH au serveur de production
- [ ] Docker et Docker Compose installés sur le serveur

## Sécurité
- [ ] `SECRET_KEY` généré (32+ caractères aléatoires)
- [ ] `DB_PASSWORD` fort (20+ caractères)
- [ ] `REDIS_PASSWORD` défini
- [ ] `SENTRY_DSN` configuré
- [ ] `DEBUG=False` en production
- [ ] `ALLOWED_HOSTS` restreint au domaine
- [ ] `CORS_ALLOWED_ORIGINS` restreint
- [ ] Ports exposés :bind sur `127.0.0.1` uniquement
- [ ] Firewall : 80, 443, SSH seulement
- [ ] 2FA / VPN pour accès SSH

## Base de données
- [ ] PgBouncer configuré (transaction pooling)
- [ ] Backup DB automatisé (cron daily)
- [ ] Backup vers S3/Glacier configuré
- [ ] Monitoring connexions actives
- [ ] `CONN_MAX_AGE=60` configuré
- [ ] Migrations appliquées

## Application
- [ ] `collectstatic` exécuté
- [ ] Celery Beat démarré (tâches périodiques)
- [ ] Superuser initial créé
- [ ] Logs JSON stdout (pas de fichiers)
- [ ] Sentry SDK actif (traces 5%)

## Monitoring
- [ ] Prometheus + Grafana déployés
- [ ] Alertes configurées (email / Slack / PagerDuty)
- [ ] Healthcheck endpoint accessible
- [ ] Logs centralisés (Loki / ELK)
- [ ] Uptime monitoring (ex: UptimeRobot, Pingdom)

## Performances
- [ ] Gzip / Brotli compression activée
- [ ] Cache Redis configuré (django cache)
- [ ] Cache navigateur (staticfiles : 1 an, media : 30 jours)
- [ ] Nginx `sendfile` / `tcp_nopush` activé
- [ ] Workers Gunicorn : `2 * CPU + 1`
- [ ] PgBouncer pool size adapté

## Déploiement
- [ ] Images Docker taguées (SHA + latest)
- [ ] Rollback plan documenté
- [ ] Smoke tests automatisés après déploiement
- [ ] Notifications équipe (Slack / Mattermost)
- [ ] Maintenance window si déploiement cassant

## Post-déploiement
- [ ] Vérifier les endpoints API (smoke tests)
- [ ] Vérifier les logs Sentry (pas d'erreurs inattendues)
- [ ] Vérifier les métriques Prometheus
- [ ] Vérifier les tâches Celery
- [ ] Vérifier la collecte des statiques
- [ ] Vérifier les backups
- [ ] Mettre à jour la documentation si nécessaire
