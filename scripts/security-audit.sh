#!/usr/bin/env bash
# ============================================================
# SECURITY AUDIT — Audit de sécurité automatisé
# ============================================================
# Usage: ./scripts/security-audit.sh
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
EXIT_CODE=0

log_pass() { echo -e "  ${GREEN}✓${NC} $1"; }
log_fail() { echo -e "  ${RED}✗${NC} $1"; EXIT_CODE=1; }
log_warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║   Security Audit — Oeuvres Sociales                ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# ── 1. Vérification des fichiers sensibles ──────────────
echo -e "${GREEN}[1] Fichiers sensibles${NC}"
for f in ".env" "backend/.env" "docker-compose.override.yml"; do
    if [ -f "$f" ]; then
        log_fail "$f présent dans le dépôt — risque de fuite de secrets"
    fi
done
[ -f "backend/.env.production" ] && log_pass "backend/.env.production présent"
[ -f "nginx/ssl/cert.pem" ] && log_pass "Certificats SSL présents" || log_warn "Certificats SSL absents"
echo ""

# ── 2. Permissions des fichiers sensibles ───────────────
echo -e "${GREEN}[2] Permissions${NC}"
if [ -f "backend/.env.production" ]; then
    local perm=$(stat -f "%Lp" "backend/.env.production" 2>/dev/null || stat -c "%a" "backend/.env.production" 2>/dev/null)
    if [ "$perm" = "600" ] || [ "$perm" = "400" ]; then
        log_pass "backend/.env.production permissions OK ($perm)"
    else
        log_fail "backend/.env.production permissions ($perm) — doit être 600"
    fi
fi
if [ -d "nginx/ssl" ]; then
    perm=$(stat -f "%Lp" "nginx/ssl" 2>/dev/null || stat -c "%a" "nginx/ssl" 2>/dev/null)
    [ "$perm" = "700" ] || [ "$perm" = "755" ] && log_pass "nginx/ssl permissions OK" || log_fail "nginx/ssl permissions ($perm)"
fi
echo ""

# ── 3. Variables d'environnement requises ───────────────
echo -e "${GREEN}[3] Variables d'environnement${NC}"
if [ -f "backend/.env.production" ]; then
    local required_vars=("SECRET_KEY" "DB_PASSWORD" "REDIS_PASSWORD" "SENTRY_DSN")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "backend/.env.production" 2>/dev/null; then
            local val=$(grep "^${var}=" "backend/.env.production" | cut -d= -f2)
            if [ "${#val}" -lt 10 ] || echo "$val" | grep -qi "changez\|changeme\|default\|CHANGE\|password\|1234"; then
                log_fail "$var a une valeur faible"
            else
                log_pass "$var définie"
            fi
        else
            log_fail "$var manquante"
        fi
    done
else
    log_fail "backend/.env.production introuvable"
fi
echo ""

# ── 4. Dépendances (pip-audit) ─────────────────────────
echo -e "${GREEN}[4] Audit des dépendances Python${NC}"
if command -v pip-audit &>/dev/null; then
    pip-audit -r backend/requirements/production.txt -r backend/requirements/base.txt 2>&1 || log_warn "Vulnérabilités détectées"
else
    log_warn "pip-audit non installé — installation recommandée: pip install pip-audit"
fi
echo ""

# ── 5. Configuration Django (sécurité) ──────────────────
echo -e "${GREEN}[5] Configuration Django${NC}"
if [ -f "backend/config/settings/production.py" ]; then
    grep -q "DEBUG = False" "backend/config/settings/production.py" && log_pass "DEBUG=False" || log_fail "DEBUG=True en production"
    grep -q "SECURE_SSL_REDIRECT = True" "backend/config/settings/production.py" && log_pass "SSL Redirect activé" || log_fail "SSL Redirect désactivé"
    grep -q "SECURE_HSTS_SECONDS" "backend/config/settings/production.py" && log_pass "HSTS activé" || log_fail "HSTS désactivé"
    grep -q "SESSION_COOKIE_SECURE = True" "backend/config/settings/production.py" && log_pass "Session cookie secure activé" || log_fail "Session cookie secure désactivé"
    grep -q "CSRF_COOKIE_HTTPONLY" "backend/config/settings/production.py" && log_pass "CSRF HttpOnly activé" || log_fail "CSRF HttpOnly désactivé"
else
    log_fail "backend/config/settings/production.py introuvable"
fi
echo ""

# ── 6. Dockerfile sécurisé ─────────────────────────────
echo -e "${GREEN}[6] Sécurité Docker${NC}"
if [ -f "docker/backend/Dockerfile" ]; then
    grep -q "USER django" "docker/backend/Dockerfile" && log_pass "Utilisateur non-root (django)" || log_fail "Application tourne en root"
fi
if [ -f "docker-compose.prod.yml" ]; then
    grep -q "restart: always" "docker-compose.prod.yml" && log_pass "Services avec restart policy"
    grep -q "127.0.0.1:" "docker-compose.prod.yml" && log_pass "Ports exposés en localhost uniquement" || log_warn "Ports exposés sur 0.0.0.0"
fi
echo ""

# ── 7. Nginx security headers ──────────────────────────
echo -e "${GREEN}[7] Sécurité Nginx${NC}"
if [ -f "nginx/conf.d/production.conf" ]; then
    grep -q "Strict-Transport-Security" "nginx/conf.d/production.conf" && log_pass "HSTS header" || log_fail "HSTS header manquant"
    grep -q "Content-Security-Policy" "nginx/conf.d/production.conf" && log_pass "CSP header" || log_fail "CSP header manquant"
    grep -q "Permissions-Policy" "nginx/conf.d/production.conf" && log_pass "Permissions Policy" || log_fail "Permissions Policy manquant"
    grep -q "X-Frame-Options" "nginx/conf.d/production.conf" && log_pass "X-Frame-Options header" || log_fail "X-Frame-Options manquant"
    grep -q "ssl_protocols TLSv1.2 TLSv1.3" "nginx/conf.d/production.conf" && log_pass "SSL protocols (TLS 1.2/1.3)" || log_fail "SSL protocols faibles"
else
    log_fail "nginx/conf.d/production.conf introuvable"
fi
echo ""

# ── Résumé ──────────────────────────────────────────────
if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "${GREEN}✓ Audit de sécurité terminé — aucun problème critique${NC}"
else
    echo -e "${RED}✗ Audit de sécurité terminé — des problèmes nécessitent votre attention${NC}"
fi
echo ""

exit $EXIT_CODE
