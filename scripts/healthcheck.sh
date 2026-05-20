#!/usr/bin/env bash
# ============================================================
# HEALTHCHECK — Vérification complète de l'infrastructure
# ============================================================
# Usage: ./scripts/healthcheck.sh [--verbose]
# ============================================================
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
VERBOSE=false
EXIT_CODE=0

[ "${1:-}" = "--verbose" ] && VERBOSE=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    local container=$2
    local expected=$3

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        local health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}' "$container" 2>/dev/null)

        if [ "$status" = "running" ] && [ "$health" = "healthy" -o "$health" = "running" ]; then
            echo -e "  ${GREEN}✓${NC} $service ($health)"
            return 0
        else
            echo -e "  ${RED}✗${NC} $service ($status/$health)"
            return 1
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} $service — container introuvable"
        return 1
    fi
}

check_endpoint() {
    local url=$1
    local expected=${2:-200}

    local status=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")

    if [ "$status" = "$expected" ] || [ "$status" = "302" ] || [ "$status" = "401" ]; then
        echo -e "  ${GREEN}✓${NC} $url → $status"
        return 0
    else
        echo -e "  ${RED}✗${NC} $url → $status (attendu: $expected)"
        return 1
    fi
}

check_db() {
    local container="oeuvres_postgres"
    local db="${POSTGRES_DB:-oeuvres_sociales}"
    local user="${POSTGRES_USER:-oeuvres_user}"

    if docker exec "$container" pg_isready -U "$user" -d "$db" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL — connexion OK"
        local size=$(docker exec "$container" psql -U "$user" -d "$db" -t -c "SELECT pg_size_pretty(pg_database_size('$db'));" 2>/dev/null | tr -d ' ')
        [ -n "$size" ] && echo -e "       Taille DB: $size"
        return 0
    else
        echo -e "  ${RED}✗${NC} PostgreSQL — connexion impossible"
        return 1
    fi
}

check_redis() {
    local container="oeuvres_redis"
    if docker exec "$container" redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "  ${GREEN}✓${NC} Redis — connexion OK"
        local info=$(docker exec "$container" redis-cli info memory | grep "used_memory_human" | cut -d: -f2)
        [ -n "$info" ] && echo -e "       Mémoire: $info"
        return 0
    else
        echo -e "  ${RED}✗${NC} Redis — connexion impossible"
        return 1
    fi
}

check_disk() {
    echo -e "  ${GREEN}✓${NC} Disque — $(df -h / | awk 'NR==2{print $5 " utilisé sur " $2}')"
}

check_ssl() {
    local domain="${SITE_URL:-oeuvres-sociales.dz}"
    if command -v openssl &>/dev/null; then
        local expiry=$(echo | openssl s_client -servername "$domain" -connect "$domain":443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
        if [ -n "$expiry" ]; then
            echo -e "  ${GREEN}✓${NC} SSL — expire le $expiry"
            return 0
        fi
    fi
    echo -e "  ${YELLOW}⚠${NC} SSL — vérification impossible"
    return 0
}

main() {
    local base_url="${SITE_URL:-http://localhost}"
    local exit_code=0

    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║   Health Check — Oeuvres Sociales                  ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""

    echo -e "${GREEN}Services Docker:${NC}"
    check_service "Backend Django"      "oeuvres_backend"       "healthy" || exit_code=1
    check_service "Celery Worker"       "oeuvres_celery_worker" "running" || exit_code=1
    check_service "Celery Beat"         "oeuvres_celery_beat"   "running" || exit_code=1
    check_service "Frontend React"      "oeuvres_frontend"      "running" || exit_code=1
    check_service "Nginx Proxy"         "oeuvres_nginx"         "running" || exit_code=1
    check_service "PostgreSQL"          "oeuvres_postgres"      "healthy" || exit_code=1
    check_service "Redis"               "oeuvres_redis"         "healthy" || exit_code=1
    echo ""

    echo -e "${GREEN}Infrastructure:${NC}"
    check_db || exit_code=1
    check_redis || exit_code=1
    check_disk
    check_ssl
    echo ""

    echo -e "${GREEN}API Endpoints:${NC}"
    check_endpoint "$base_url/api/v1/auth/verify/" || exit_code=1
    check_endpoint "$base_url/" || exit_code=1
    echo ""

    if [ "$exit_code" -eq 0 ]; then
        echo -e "${GREEN}✓ Tous les contrôles sont OK${NC}"
    else
        echo -e "${RED}✗ Certains contrôles ont échoué — vérifiez les logs${NC}"
    fi
    echo ""

    return $exit_code
}

main
