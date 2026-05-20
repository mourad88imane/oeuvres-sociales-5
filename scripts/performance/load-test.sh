#!/usr/bin/env bash
# ============================================================
# PERFORMANCE TEST — Benchmark et vérification performances
# ============================================================
# Usage: ./scripts/performance/load-test.sh [url]
#   url → Base URL de l'API (défaut: http://localhost)
# ============================================================
set -euo pipefail

BASE_URL="${1:-http://localhost}"
REPORT_DIR="reports/performance"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$REPORT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Vérifier qu'il n'y a pas de K6 ou Apache Bench ─────
check_tools() {
    if command -v k6 &>/dev/null; then
        log_info "k6 trouvé"
        K6=true
    else
        log_warn "k6 non installé — installation: brew install k6"
        K6=false
    fi
    if command -v ab &>/dev/null; then
        log_info "Apache Bench (ab) trouvé"
        AB=true
    else
        log_warn "ab non installé — installation: brew install apr"
        AB=false
    fi
    if ! $K6 && ! $AB; then
        log_error "Aucun outil de benchmark disponible"
        exit 1
    fi
}

# ── Test 1 : Latence API (endpoint simple) ──────────────
test_latency() {
    log_info "Test 1 : Latence API..."
    local total_time=0
    local max_time=0
    local min_time=999

    for i in $(seq 1 20); do
        local start=$(date +%s%N)
        curl -sf -o /dev/null "$BASE_URL/api/v1/auth/verify/" 2>/dev/null || true
        local end=$(date +%s%N)
        local elapsed=$(( (end - start) / 1000000 ))
        total_time=$((total_time + elapsed))
        [ "$elapsed" -gt "$max_time" ] && max_time=$elapsed
        [ "$elapsed" -lt "$min_time" ] && min_time=$elapsed
    done

    local avg=$(( total_time / 20 ))
    echo "  Latence moyenne: ${avg}ms"
    echo "  Latence min:     ${min_time}ms"
    echo "  Latence max:     ${max_time}ms"
}

# ── Test 2 : Débit (ab) ──────────────────────────────────
test_throughput() {
    if $AB; then
        log_info "Test 2 : Débit (ab -n 1000 -c 10)..."
        ab -n 1000 -c 10 -k "$BASE_URL/api/v1/auth/verify/" > "$REPORT_DIR/ab_report_$DATE.txt" 2>&1
        grep -E "Requests per second|Failed requests|Time per request" "$REPORT_DIR/ab_report_$DATE.txt" | head -3
    fi
}

# ── Test 3 : k6 (spike test) ─────────────────────────────
test_k6() {
    if $K6; then
        log_info "Test 3 : k6 — test de charge progressif..."

        cat > /tmp/k6_script.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');

export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 100 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],
        errors: ['rate<0.1'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost';

export default function () {
    const endpoints = [
        { url: `${BASE_URL}/api/v1/ai/health/`, method: 'GET' },
        { url: `${BASE_URL}/api/v1/monitoring/health/`, method: 'GET' },
    ];

    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
    const res = http.get(endpoint.url);

    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });

    errorRate.add(res.status !== 200);
    latencyTrend.add(res.timings.duration);
    sleep(1);
}
EOF

        BASE_URL="$BASE_URL" k6 run /tmp/k6_script.js --out json="$REPORT_DIR/k6_report_$DATE.json" > "$REPORT_DIR/k6_output_$DATE.txt" 2>&1 || true
        grep -E "http_req_duration|http_reqs|http_req_failed" "$REPORT_DIR/k6_output_$DATE.txt" | head -5
    fi
}

# ── Test 4 : Temps de réponse DB ─────────────────────────
test_db_perf() {
    log_info "Test 4 : Performance base de données..."
    docker exec oeuvres_postgres psql -U oeuvres_user -d oeuvres_sociales -c "
        SELECT 'Connexions actives' as check, count(*) as value FROM pg_stat_activity;
    " 2>/dev/null | head -5 || log_warn "Impossible de se connecter à la DB"
}

# ── Recommandations ──────────────────────────────────────
recommendations() {
    echo ""
    echo -e "${YELLOW}Recommandations d'optimisation :${NC}"
    echo "  - Cible p95 < 500ms pour les endpoints API"
    echo "  - Activer le cache Redis pour les requêtes fréquentes"
    echo "  - Vérifier les requêtes N+1 dans les sérializers"
    echo "  - Utiliser select_related / prefetch_related"
    echo "  - Ajouter des index sur les colonnes de filtre fréquentes"
    echo "  - Considérer PgBouncer pour les connexions DB"
    echo "  - Vérifier que CONN_MAX_AGE=60 est configuré"
    echo "  - Activer la compression Gzip Nginx"
}

# ── Main ──────────────────────────────────────────────────
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║   Performance Tests — Oeuvres Sociales        ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""

    check_tools
    echo ""
    test_latency
    echo ""
    test_db_perf
    echo ""
    test_throughput
    echo ""
    test_k6
    echo ""
    recommendations
    echo ""
    log_info "Rapports sauvegardés dans $REPORT_DIR/"
}

main
