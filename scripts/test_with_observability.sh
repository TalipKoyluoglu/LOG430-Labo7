#!/bin/bash

# Script pour lancer un test de charge avec observabilité
# Usage: ./scripts/test_with_observability.sh [baseline|stress]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
TEST_TYPE=${1:-baseline}
# Utiliser le deuxième argument comme étiquette, ou un timestamp par défaut
LABEL=${2:-$(date +"%Y%m%d_%H%M%S")}
RESULTS_DIR="results"
FILENAME_BASE="${RESULTS_DIR}/${TEST_TYPE}_${LABEL}"

# Vérification des prérequis
check_prerequisites() {
    print_header "Vérification des prérequis"
    
    # Vérifier que k6 est installé
    if ! command -v k6 &> /dev/null; then
        print_error "k6 n'est pas installé"
        exit 1
    fi
    print_info "k6 est installé: $(k6 version)"
    
    # Vérifier que l'application Django fonctionne
    if ! curl -s http://localhost:8000/api/v1/reports/ > /dev/null; then
        print_error "L'application Django n'est pas accessible"
        exit 1
    fi
    print_info "Application Django accessible"
    
    # Vérifier que Prometheus fonctionne
    if ! curl -s http://localhost:9090/-/healthy > /dev/null; then
        print_warning "Prometheus n'est pas accessible. Démarrage..."
        ./scripts/start_observability.sh
    else
        print_info "Prometheus est accessible"
    fi
    
    # Créer le dossier results
    mkdir -p "$RESULTS_DIR"
}

# Lancer le test de charge
run_load_test() {
    print_header "Lancement du test de charge: $TEST_TYPE (Étiquette: $LABEL)"
    
    local script_file=""
    
    case $TEST_TYPE in
        "baseline")
            script_file="scripts/load_test_baseline.js"
            print_info "Test de base avec montée progressive"
            ;;
        "stress")
            script_file="scripts/stress_test.js"
            print_warning "Test de stress - attention aux performances"
            ;;
        *)
            print_error "Type de test invalide: $TEST_TYPE"
            print_info "Utilisez 'baseline' ou 'stress'"
            exit 1
            ;;
    esac
    
    # Lancer le test avec k6
    print_info "Démarrage du test..."
    k6 run \
        --out json="${FILENAME_BASE}.json" \
        --out csv="${FILENAME_BASE}.csv" \
        "$script_file"
    
    print_info "Test terminé. Résultats sauvegardés dans ${FILENAME_BASE}.json/.csv"
}

# Analyser les résultats
analyze_results() {
    print_header "Analyse des résultats"
    
    local result_file="${FILENAME_BASE}.json"
    
    if [ -f "$result_file" ]; then
        print_info "Fichier de résultats: $result_file"
        
        # Extraire les métriques clés avec jq (si disponible)
        if command -v jq &> /dev/null; then
            print_info "Métriques clés:"
            echo "  - Requêtes totales: $(jq -r '.metrics.http_reqs.values.count' "$result_file")"
            echo "  - Temps de réponse moyen: $(jq -r '.metrics.http_req_duration.values.avg' "$result_file") ms"
            echo "  - Taux d'erreur: $(jq -r '.metrics.http_req_failed.values.rate' "$result_file")"
            echo "  - Requêtes/sec: $(jq -r '.metrics.http_reqs.values.rate' "$result_file")"
        else
            print_warning "jq n'est pas installé. Impossible d'analyser automatiquement les résultats."
        fi
    else
        print_warning "Fichier de résultats non trouvé"
    fi
}

# Afficher les liens d'accès
show_access_links() {
    print_header "Liens d'accès"
    
    echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Métriques Django:${NC} http://localhost:8000/metrics"
    echo ""
    echo -e "${YELLOW}Pour voir les métriques en temps réel:${NC}"
    echo "1. Ouvrez Grafana dans votre navigateur"
    echo "2. Connectez-vous avec admin/admin"
    echo "3. Allez dans Dashboards > 4 Golden Signals"
    echo "4. Lancez un nouveau test pour voir les métriques en temps réel"
}

# Fonction principale
main() {
    check_prerequisites
    run_load_test
    analyze_results
    show_access_links
}

# Exécution
main "$@" 