#!/usr/bin/env bash
# ============================================================
# ROTATE LOGS — Rotation des logs Docker et application
# ============================================================
# Usage: ./scripts/rotate-logs.sh
# Ajouter dans crontab :
#   0 3 * * * /opt/oeuvres-sociales/scripts/rotate-logs.sh
# ============================================================
set -euo pipefail

LOG_DIR="/opt/oeuvres-sociales/backend/logs"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d)

# ── Rotation des logs applicatifs ─────────────────────────
if [ -d "$LOG_DIR" ]; then
    find "$LOG_DIR" -name "*.log" -type f -exec sh -c '
        mv "$1" "${1%.log}_'$DATE'.log"
        gzip -9 "${1%.log}_'$DATE'.log"
    ' _ {} \;

    # Nettoyage des logs compressés de plus de $RETENTION_DAYS jours
    find "$LOG_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \;
fi

# ── Nettoyage des logs Docker ─────────────────────────────
docker system df 2>/dev/null
docker container prune -f --filter "until=24h" 2>/dev/null || true
docker image prune -f --filter "until=24h" 2>/dev/null || true

# ── Rotation des logs Nginx ──────────────────────────────
docker exec oeuvres_nginx sh -c '
    mv /var/log/nginx/access.log /var/log/nginx/access.log.'$DATE' 2>/dev/null || true
    mv /var/log/nginx/error.log /var/log/nginx/error.log.'$DATE' 2>/dev/null || true
    kill -USR1 $(cat /var/run/nginx.pid) 2>/dev/null || nginx -s reopen
    find /var/log/nginx -name "*.log.*" -mtime +'$RETENTION_DAYS' -exec rm -f {} \;
' 2>/dev/null || true

echo "[$(date)] Rotation des logs terminée — conservés $RETENTION_DAYS jours"
