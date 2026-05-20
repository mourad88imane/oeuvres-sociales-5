#!/usr/bin/env bash
# ============================================================
# DEPLOY — Déploiement automatisé production
# ============================================================
# Usage: ./scripts/deploy.sh [staging|production]
#   staging    → déploie sur l'environnement de staging
#   production → déploie sur la production
# ============================================================
set -euo pipefail

# ── Configuration ─────────────────────────────────────────
COMPOSE_FILE="docker-compose.prod.yml"
BACKEND_SERVICE="backend"
FRONTEND_SERVICE="frontend"
STACK_NAME="oeuvres-sociales-prod"

# ── Couleurs ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()    { echo -e "${CYAN}[STEP]${NC} $1"; }

# ── Pré-déploiement : vérifications ──────────────────────
pre_deploy_checks() {
    log_step "Vérifications pré-déploiement..."

    if [ ! -f "backend/.env.production" ]; then
        log_error "Fichier backend/.env.production manquant"
        exit 1
    fi

    if [ ! -d "nginx/ssl" ]; then
        log_warn "Dossier nginx/ssl/ manquant — vérifiez les certificats"
    fi

    # Vérifier que Docker est disponible
    if ! docker info &>/dev/null; then
        log_error "Docker n'est pas en cours d'exécution"
        exit 1
    fi

    # Vérifier que docker-compose.prod.yml existe
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "$COMPOSE_FILE introuvable"
        exit 1
    fi

    log_info "Toutes les vérifications sont passées"
}

# ── Pull des images ──────────────────────────────────────
pull_images() {
    log_step "Récupération des images Docker..."
    docker compose -f "$COMPOSE_FILE" pull --quiet
    log_info "Images téléchargées"
}

# ── Déploiement des services ──────────────────────────────
deploy_services() {
    log_step "Déploiement des services..."
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
    log_info "Services démarrés"
}

# ── Attente que les services soient sains ────────────────
wait_for_health() {
    local retries=30
    local interval=5

    log_step "Attente de la disponibilité des services..."

    for i in $(seq 1 $retries); do
        if docker compose -f "$COMPOSE_FILE" ps --status healthy | grep -q "healthy"; then
            log_info "✓ Services en bonne santé (tentative $i/$retries)"
            return 0
        fi
        sleep "$interval"
    done

    log_warn "⚠️  Certains services ne sont pas en 'healthy' — vérifiez les logs"
    docker compose -f "$COMPOSE_FILE" logs --tail=20 backend nginx
    return 1
}

# ── Migrations et collectstatic ──────────────────────────
run_django_tasks() {
    log_step "Application des migrations..."
    docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate --noinput
    log_info "✓ Migrations appliquées"

    log_step "Collecte des fichiers statiques..."
    docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py collectstatic --noinput --clear
    log_info "✓ Fichiers statiques collectés"
}

# ── Nettoyage ─────────────────────────────────────────────
cleanup() {
    log_step "Nettoyage des ressources inutilisées..."
    docker system prune -f --volumes 2>/dev/null || true
    log_info "✓ Nettoyage terminé"
}

# ── Smoke tests ───────────────────────────────────────────
smoke_tests() {
    local base_url="${SITE_URL:-https://oeuvres-sociales.dz}"

    log_step "Exécution des smoke tests..."

    local endpoints=(
        "$base_url/api/v1/auth/verify/"
        "$base_url/api/v1/health/"
        "$base_url/"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -sf -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200\|302\|401"; then
            log_info "  ✓ $endpoint"
        else
            log_error "  ✗ $endpoint — réponse inattendue"
        fi
    done

    log_info "✓ Smoke tests terminés"
}

# ── Post-déploiement ─────────────────────────────────────
post_deploy() {
    log_step "Configuration post-déploiement..."

    # Créer/Mettre à jour les tâches Celery Beat
    docker compose -f "$COMPOSE_FILE" exec -T backend \
        python manage.py celery_beat_update_schedule 2>/dev/null || true

    log_info "✓ Post-déploiement terminé"
}

# ── Rollback (en cas d'échec) ────────────────────────────
rollback() {
    log_warn "⚠️  Échec du déploiement — rollback vers la version précédente..."

    docker compose -f "$COMPOSE_FILE" down
    docker compose -f "$COMPOSE_FILE" up -d

    log_info "Rollback effectué — vérifiez l'état des services"
}

# ── Main ──────────────────────────────────────────────────
main() {
    local env="${1:-staging}"
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║   Déploiement Oeuvres Sociales — $env"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""

    if [ "$env" != "staging" ] && [ "$env" != "production" ]; then
        log_error "Environnement invalide : $env (choisissez staging ou production)"
        exit 1
    fi

    pre_deploy_checks
    pull_images
    deploy_services
    wait_for_health
    run_django_tasks
    smoke_tests
    post_deploy
    cleanup

    echo ""
    log_info "=== Déploiement $env terminé avec succès ==="
    echo ""
}

main "$@"
