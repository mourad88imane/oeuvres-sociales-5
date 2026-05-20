#!/usr/bin/env bash
# ============================================================
# BACKUP — Sauvegarde complète (DB + fichiers + configuration)
# ============================================================
# Usage: ./scripts/backup.sh [full|db|files|config]
#   full   → tout (par défaut)
#   db     → PostgreSQL uniquement
#   files  → medias uniquement
#   config → fichiers de configuration
# ============================================================
set -euo pipefail

# ── Configuration ─────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/oeuvres-sociales}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-s3://oeuvres-sociales-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Charger les variables d'environnement Docker
COMPOSE_FILE="docker-compose.prod.yml"
DB_CONTAINER="oeuvres_postgres"
BACKEND_CONTAINER="oeuvres_backend"

# ── Couleurs ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Logging ───────────────────────────────────────────────
log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Vérifications ─────────────────────────────────────────
check_prereqs() {
    mkdir -p "$BACKUP_DIR"/{db,files,config}
    if ! command -v docker &>/dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
}

# ── Backup PostgreSQL ─────────────────────────────────────
backup_db() {
    local backup_file="$BACKUP_DIR/db/oeuvres_db_$DATE.sql.gz"
    log_info "Sauvegarde de la base de données..."
    docker compose -f "$COMPOSE_FILE" exec -T "$DB_CONTAINER" \
        pg_dump -U "${POSTGRES_USER:-oeuvres_user}" -d "${POSTGRES_DB:-oeuvres_sociales}" \
        --no-owner --no-acl \
        --compress=9 \
        --file=/backups/db/dump_$DATE.sql.gz
    log_info "✓ Base sauvegardée : $backup_file ($(du -h "$backup_file" | cut -f1))"
}

# ── Backup fichiers (media) ───────────────────────────────
backup_files() {
    log_info "Sauvegarde des fichiers media..."
    local backup_file="$BACKUP_DIR/files/media_$DATE.tar.gz"
    docker compose -f "$COMPOSE_FILE" exec -T "$BACKEND_CONTAINER" \
        tar czf - /app/media > "$backup_file"
    log_info "✓ Media sauvegardé : $backup_file ($(du -h "$backup_file" | cut -f1))"
}

# ── Backup configuration ──────────────────────────────────
backup_config() {
    log_info "Sauvegarde de la configuration..."
    local backup_file="$BACKUP_DIR/config/config_$DATE.tar.gz"
    tar czf "$backup_file" \
        docker-compose.yml \
        docker-compose.prod.yml \
        nginx/conf.d/ \
        backend/.env.production \
        backend/config/settings/ \
        2>/dev/null || true
    log_info "✓ Configuration sauvegardée : $backup_file ($(du -h "$backup_file" | cut -f1))"
}

# ── Nettoyage des backups anciens ─────────────────────────
cleanup_old() {
    log_info "Nettoyage des backups de plus de $RETENTION_DAYS jours..."
    find "$BACKUP_DIR/db"     -name "*.sql.gz" -mtime +$RETENTION_DAYS -exec rm -v {} \;
    find "$BACKUP_DIR/files"  -name "*.tar.gz" -mtime +$RETENTION_DAYS -exec rm -v {} \;
    find "$BACKUP_DIR/config" -name "*.tar.gz" -mtime +$RETENTION_DAYS -exec rm -v {} \;
    log_info "✓ Nettoyage terminé"
}

# ── Synchronisation S3 (optionnel) ───────────────────────
sync_s3() {
    if command -v aws &>/dev/null && aws s3 ls "$S3_BUCKET" &>/dev/null; then
        log_info "Synchronisation vers S3..."
        aws s3 sync "$BACKUP_DIR" "$S3_BUCKET/$(date +%Y/%m)" --storage-class GLACIER
        log_info "✓ Synchronisation S3 terminée"
    else
        log_warn "AWS CLI non disponible ou bucket inaccessible — skipping S3"
    fi
}

# ── Vérification des backups ──────────────────────────────
verify_backups() {
    log_info "Vérification de l'intégrité des backups..."
    for f in "$BACKUP_DIR/db"/*.sql.gz; do
        if [ -f "$f" ] && gzip -t "$f" 2>/dev/null; then
            log_info "  ✓ $(basename "$f")"
        else
            log_error "  ✗ $(basename "$f") — fichier corrompu"
        fi
    done
}

# ── Main ──────────────────────────────────────────────────
main() {
    check_prereqs

    case "${1:-full}" in
        full)
            backup_db
            backup_files
            backup_config
            cleanup_old
            sync_s3
            verify_backups
            log_info "=== Sauvegarde complète terminée ==="
            ;;
        db)
            backup_db
            ;;
        files)
            backup_files
            ;;
        config)
            backup_config
            ;;
        *)
            echo "Usage: $0 [full|db|files|config]"
            exit 1
            ;;
    esac
}

main "$@"
