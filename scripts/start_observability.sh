#!/bin/bash

# Script pour démarrer l'observabilité (Prometheus + Grafana)
# Usage: ./scripts/start_observability.sh

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

# Vérification des prérequis
check_prerequisites() {
    print_header "Vérification des prérequis"
    
    # Vérifier que Docker est installé
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi
    print_info "Docker est installé"
    
    # Vérifier que Docker Compose est installé
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi
    print_info "Docker Compose est installé"
    
    # Vérifier que l'application Django fonctionne
    if ! curl -s http://localhost:8000/api/v1/reports/ > /dev/null; then
        print_error "L'application Django n'est pas accessible sur http://localhost:8000"
        print_warning "Assurez-vous que le serveur Django est démarré"
        exit 1
    fi
    print_info "Application Django accessible"
}

# Démarrer Prometheus et Grafana
start_observability() {
    print_header "Démarrage de l'observabilité"
    
    # Arrêter les conteneurs existants s'ils existent
    docker-compose down 2>/dev/null || true
    
    # Démarrer les services
    print_info "Démarrage de Prometheus et Grafana..."
    docker-compose up -d
    
    # Attendre que les services démarrent
    print_info "Attente du démarrage des services..."
    sleep 10
    
    # Vérifier que Prometheus fonctionne
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        print_info "Prometheus est démarré sur http://localhost:9090"
    else
        print_warning "Prometheus pourrait ne pas être encore prêt"
    fi
    
    # Vérifier que Grafana fonctionne
    if curl -s http://localhost:3000/api/health > /dev/null; then
        print_info "Grafana est démarré sur http://localhost:3000"
        print_info "Login: admin / admin"
    else
        print_warning "Grafana pourrait ne pas être encore prêt"
    fi
}

# Afficher les informations d'accès
show_access_info() {
    print_header "Informations d'accès"
    
    echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Métriques Django:${NC} http://localhost:8000/metrics"
    echo ""
    echo -e "${YELLOW}Prochaines étapes:${NC}"
    echo "1. Ouvrir Grafana et vous connecter"
    echo "2. Vérifier que la source de données Prometheus est configurée"
    echo "3. Importer le dashboard '4 Golden Signals'"
    echo "4. Lancer un test de charge pour voir les métriques"
}

# Fonction principale
main() {
    check_prerequisites
    start_observability
    show_access_info
}

# Exécution
main "$@" 