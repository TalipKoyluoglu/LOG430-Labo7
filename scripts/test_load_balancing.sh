#!/bin/bash

# Script de test du load balancing via Kong API Gateway
# Utilise curl, K6 et analyse les logs Kong

echo "🧪 Test du Load Balancing via Kong API Gateway"
echo "=============================================="

# Configuration
API_KEY="magasin-secret-key-2025"
KONG_URL="http://localhost:8080"
KONG_ADMIN_URL="http://localhost:8081"
TEST_ENDPOINT="/api/catalogue/"

# Fonction pour vérifier que Kong est accessible
check_kong_ready() {
    echo "🔍 Vérification de Kong..."
    if ! curl -s "$KONG_ADMIN_URL" > /dev/null; then
        echo "❌ Kong Admin API non accessible sur $KONG_ADMIN_URL"
        echo "💡 Assurez-vous que Kong est démarré avec docker-compose up"
        exit 1
    fi
    
    if ! curl -s "$KONG_URL" > /dev/null; then
        echo "❌ Kong Gateway non accessible sur $KONG_URL"
        exit 1
    fi
    
    echo "✅ Kong est accessible"
}

# Fonction pour afficher la configuration de l'upstream
show_upstream_config() {
    echo "📊 Configuration de l'upstream catalogue:"
    echo "----------------------------------------"
    
    # Informations sur l'upstream
    echo "🔧 Upstream catalogue-upstream:"
    curl -s "$KONG_ADMIN_URL/upstreams/catalogue-upstream" | jq -r '.algorithm // "Non configuré"' | sed 's/^/   Algorithme: /'
    
    # Liste des targets
    echo "🎯 Targets configurés:"
    curl -s "$KONG_ADMIN_URL/upstreams/catalogue-upstream/targets" | jq -r '.data[] | "   - " + .target + " (poids: " + (.weight|tostring) + ")"' 2>/dev/null || echo "   ⚠️  Aucun target configuré"
    
    # Santé des targets
    echo "🏥 Santé des targets:"
    curl -s "$KONG_ADMIN_URL/upstreams/catalogue-upstream/health" | jq -r '.data[] | "   - " + .target + ": " + .health' 2>/dev/null || echo "   ⚠️  Impossible de vérifier la santé"
    
    echo ""
}

# Test simple avec curl en boucle
test_with_curl() {
    echo "🔄 Test avec curl (10 requêtes):"
    echo "--------------------------------"
    
    # Nettoyer les logs Kong
    docker exec $(docker ps -q -f name=kong) sh -c "echo '' > /tmp/kong-access.log" 2>/dev/null
    
    for i in {1..10}; do
        echo -n "Requête $i: "
        response=$(curl -s -w "%{http_code}" -H "X-API-Key: $API_KEY" "$KONG_URL$TEST_ENDPOINT")
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Succès"
        else
            echo "❌ Échec (code: $http_code)"
        fi
        
        sleep 0.5
    done
    
    echo ""
}

# Analyse des logs Kong pour détecter la répartition
analyze_kong_logs() {
    echo "📈 Analyse des logs Kong:"
    echo "------------------------"
    
    # Récupérer les logs Kong
    log_content=$(docker exec $(docker ps -q -f name=kong) cat /tmp/kong-access.log 2>/dev/null)
    
    if [ -z "$log_content" ]; then
        echo "⚠️  Aucun log Kong trouvé"
        return
    fi
    
    # Compter les requêtes par upstream target
    echo "🎯 Répartition des requêtes par instance:"
    echo "$log_content" | grep -o '"upstream_uri":"[^"]*"' | sort | uniq -c | sed 's/.*upstream_uri":"http:\/\/\([^"]*\)".*/\1/' | while read count target; do
        echo "   $target: $count requêtes"
    done
    
    # Statistiques générales
    total_requests=$(echo "$log_content" | grep -c '"request"')
    echo "📊 Total des requêtes loggées: $total_requests"
    
    echo ""
}

# Test avec K6 si disponible
test_with_k6() {
    echo "🚀 Test avec K6 (si disponible):"
    echo "--------------------------------"
    
    if command -v k6 &> /dev/null; then
        echo "✅ K6 détecté, lancement du test de charge..."
        k6 run scripts/load_balancing_test.js
    else
        echo "⚠️  K6 non installé, test ignoré"
        echo "💡 Installez K6 pour des tests de charge avancés:"
        echo "   curl -s https://dl.k6.io/key.gpg | sudo apt-key add -"
        echo "   echo 'deb https://dl.k6.io/deb stable main' | sudo tee /etc/apt/sources.list.d/k6.list"
        echo "   sudo apt update && sudo apt install k6"
    fi
    
    echo ""
}

# Test de failover (simulation de panne)
test_failover() {
    echo "🔧 Test de failover (simulation de panne):"
    echo "------------------------------------------"
    
    echo "📋 Instances actuellement actives:"
    show_upstream_config
    
    echo "🛑 Simulation d'arrêt d'une instance (catalogue-service-2)..."
    docker stop log430-labo5-catalogue-service-2-1 2>/dev/null || echo "   ⚠️  Service catalogue-service-2 non trouvé"
    
    sleep 5
    
    echo "🧪 Test de 5 requêtes après arrêt:"
    for i in {1..5}; do
        echo -n "Requête $i: "
        response=$(curl -s -w "%{http_code}" -H "X-API-Key: $API_KEY" "$KONG_URL$TEST_ENDPOINT")
        http_code="${response: -3}"
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Succès (failover fonctionne)"
        else
            echo "❌ Échec (code: $http_code)"
        fi
        
        sleep 1
    done
    
    echo "🔄 Redémarrage de l'instance..."
    docker start log430-labo5-catalogue-service-2-1 2>/dev/null || echo "   ⚠️  Impossible de redémarrer"
    
    echo "⏳ Attente de 10s pour stabilisation..."
    sleep 10
    
    echo ""
}

# Fonction principale
main() {
    check_kong_ready
    show_upstream_config
    test_with_curl
    analyze_kong_logs
    test_with_k6
    
    echo "🤔 Voulez-vous tester le failover ? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        test_failover
    fi
    
    echo "📊 Résumé des métriques disponibles:"
    echo "-----------------------------------"
    echo "🔗 Kong Admin API: $KONG_ADMIN_URL"
    echo "📈 Prometheus (si configuré): http://localhost:9090"
    echo "📊 Grafana (si configuré): http://localhost:3000"
    echo "📋 Logs Kong: docker exec <kong-container> cat /tmp/kong-access.log"
    
    echo ""
    echo "🎉 Tests de load balancing terminés !"
}

# Exécution
main "$@" 