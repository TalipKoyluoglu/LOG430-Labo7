#!/bin/bash

# Script pour exécuter les tests microservices DDD
# Usage: ./scripts/run_tests.sh [unit|e2e|integration|all|ci]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.yml"
KONG_SETUP_SCRIPT="./scripts/setup-kong.sh"

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour attendre que les services soient prêts
wait_for_services() {
    log_info "Attente que tous les services soient prêts..."
    
    # Attendre Kong Gateway
    for i in {1..30}; do
        if curl -f http://localhost:8080/ >/dev/null 2>&1; then
            log_success "Kong Gateway est prêt"
            break
        fi
        echo -n "."
        sleep 2
        if [ $i -eq 30 ]; then
            log_error "Kong Gateway n'est pas prêt après 60 secondes"
            return 1
        fi
    done
    
    # Attendre les microservices via Kong
    local services=(
        "http://localhost:8080/api/catalogue/api/ddd/catalogue/health/"
        "http://localhost:8080/api/inventaire/health/"
        "http://localhost:8080/api/ecommerce/health/"
    )
    
    for service in "${services[@]}"; do
        for i in {1..15}; do
            if curl -f -H "X-API-Key: magasin-secret-key-2025" "$service" >/dev/null 2>&1; then
                log_success "Service $(basename $(dirname $service)) est prêt"
                break
            fi
            echo -n "."
            sleep 2
            if [ $i -eq 15 ]; then
                log_warning "Service $(basename $(dirname $service)) peut ne pas être prêt"
            fi
        done
    done
}

# Tests unitaires (rapides - sans services externes)
run_unit_tests() {
    log_info "=== TESTS UNITAIRES ==="
    log_info "Tests Django frontend (magasin/tests/test_unitaires.py)"
    
    # Vérifier que Redis est disponible pour le cache Django
    if ! nc -z localhost 6379; then
        log_info "Démarrage Redis pour le cache Django..."
        docker-compose up -d redis
        sleep 5
    fi
    
    # Exécuter migrations
    python manage.py migrate
    
    # Tests unitaires
    pytest magasin/tests/test_unitaires.py -v --tb=short
    log_success "Tests unitaires terminés"
}

# Tests End-to-End (via frontend Django)
run_e2e_tests() {
    log_info "=== TESTS END-TO-END ==="
    log_info "Tests via interface Django (mocking des microservices)"
    
    # Assurer Redis pour le cache Django
    if ! nc -z localhost 6379; then
        log_info "Démarrage Redis pour le cache Django..."
        docker-compose up -d redis
        sleep 5
    fi
    
    # Migrations Django
    python manage.py migrate
    
    # Tests E2E avec mocks
    pytest tests/e2e/ -v --tb=short -m e2e
    log_success "Tests E2E terminés"
}

# Tests d'intégration (avec microservices réels)
run_integration_tests() {
    log_info "=== TESTS D'INTÉGRATION ==="
    log_info "Tests avec microservices réels via Kong Gateway"
    
    # Démarrer tous les services
    log_info "Démarrage environnement microservices complet..."
    docker-compose up -d
    
    # Attendre que tout soit prêt
    sleep 60
    wait_for_services
    
    # Configurer Kong Gateway
    if [ -f "$KONG_SETUP_SCRIPT" ]; then
        log_info "Configuration Kong Gateway..."
        chmod +x "$KONG_SETUP_SCRIPT"
        "$KONG_SETUP_SCRIPT"
        sleep 10
    else
        log_warning "Script setup Kong non trouvé: $KONG_SETUP_SCRIPT"
    fi
    
    # Tests d'intégration
    KONG_GATEWAY_URL=http://localhost:8080 \
    KONG_ADMIN_URL=http://localhost:8081 \
    pytest tests/integration/ -v --tb=short -m integration --maxfail=3
    
    log_success "Tests d'intégration terminés"
}

# Tous les tests
run_all_tests() {
    log_info "=== EXÉCUTION DE TOUS LES TESTS ==="
    
    run_unit_tests
    echo ""
    run_e2e_tests
    echo ""
    run_integration_tests
    
    log_success "Tous les tests terminés avec succès!"
}

# Simulation pipeline CI
run_ci_tests() {
    log_info "=== SIMULATION PIPELINE CI ==="
    
    # Phase 1: Tests unitaires + E2E
    log_info "Phase 1: Tests unitaires et E2E"
    run_unit_tests
    run_e2e_tests
    
    # Phase 2: Tests d'intégration
    log_info "Phase 2: Tests d'intégration microservices"
    run_integration_tests
    
    # Phase 3: Test de charge rapide
    log_info "Phase 3: Test de charge Kong (si k6 disponible)"
    if command -v k6 >/dev/null 2>&1; then
        cat > /tmp/load_test_quick.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 5,
  duration: '15s',
};

export default function() {
  const headers = { 'X-API-Key': 'magasin-secret-key-2025' };
  let response = http.get('http://localhost:8080/api/catalogue/api/ddd/catalogue/rechercher/', { headers });
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
EOF
        k6 run /tmp/load_test_quick.js
        log_success "Test de charge terminé"
    else
        log_warning "k6 non installé - test de charge ignoré"
    fi
    
    log_success "Simulation CI terminée avec succès!"
}

# Nettoyage
cleanup() {
    log_info "Nettoyage de l'environnement..."
    docker-compose down --remove-orphans >/dev/null 2>&1 || true
    log_success "Nettoyage terminé"
}

# Affichage de l'aide
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  unit        Tests unitaires (rapides, sans services externes)"
    echo "  e2e         Tests end-to-end (frontend Django avec mocks)"
    echo "  integration Tests d'intégration (microservices réels + Kong)"
    echo "  all         Tous les tests (unit + e2e + integration)"
    echo "  ci          Simulation pipeline CI complète"
    echo "  clean       Nettoyage environnement Docker"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 unit                    # Tests rapides"
    echo "  $0 integration            # Tests avec microservices"
    echo "  $0 ci                     # Simulation complète CI"
    echo "  $0 clean                  # Nettoyer Docker"
}

# Main
main() {
    case "${1:-help}" in
        "unit")
            run_unit_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "all")
            run_all_tests
            ;;
        "ci")
            run_ci_tests
            ;;
        "clean")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Option invalide: $1"
            show_help
            exit 1
            ;;
    esac
}

# Gestion des signaux pour cleanup
trap cleanup EXIT

# Vérifications préliminaires
if [ ! -f "manage.py" ]; then
    log_error "Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    log_error "Fichier docker-compose.yml non trouvé"
    exit 1
fi

# Exécution
main "$@" 