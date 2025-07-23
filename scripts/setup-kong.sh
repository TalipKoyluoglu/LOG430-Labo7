#!/bin/bash

# Activer le mode debug pour voir toutes les commandes exécutées
set -x

# Script de configuration automatique Kong
# Vérifie si les services existent déjà avant de les créer
# Inclut la configuration du load balancing

echo "🚀 Configuration Kong API Gateway avec Load Balancing..."

# Attendre que Kong soit prêt
echo "⏳ Attente de Kong..."
until curl -s http://kong:8001 > /dev/null 2>&1; do
    echo "   Kong pas encore prêt, attente 2s..."
    sleep 2
done
echo "✅ Kong est prêt !"

# Fonction pour créer un upstream s'il n'existe pas
create_upstream_if_not_exists() {
    local upstream_name=$1
    local algorithm=$2
    
    echo "🔍 Vérification de l'upstream '$upstream_name'..."
    
    # Vérifier si l'upstream existe déjà avec debug
    local check_response=$(curl -s -w "%{http_code}" "http://kong:8001/upstreams/$upstream_name")
    local http_code="${check_response: -3}"
    local response_body="${check_response%???}"
    
    echo "   Code HTTP: $http_code"
    echo "   Réponse: $response_body"
    
    if [ "$http_code" = "200" ]; then
        echo "   ⚠️  Upstream '$upstream_name' existe déjà, ignoré"
    else
        echo "   ➕ Création de l'upstream '$upstream_name' avec algorithme '$algorithm'"
        local create_response=$(curl -s -w "%{http_code}" -X POST http://kong:8001/upstreams/ \
            --data "name=$upstream_name" \
            --data "algorithm=$algorithm")
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Upstream '$upstream_name' créé"
        else
            echo "   ❌ Erreur création upstream '$upstream_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

# Fonction pour ajouter un target à un upstream s'il n'existe pas
create_target_if_not_exists() {
    local upstream_name=$1
    local target_url=$2
    local weight=$3
    
    echo "🔍 Vérification du target '$target_url' dans '$upstream_name'..."
    
    # Vérifier si le target existe déjà
    local targets_response=$(curl -s -w "%{http_code}" "http://kong:8001/upstreams/$upstream_name/targets")
    local targets_code="${targets_response: -3}"
    local targets_body="${targets_response%???}"
    
    echo "   Code vérification targets: $targets_code"
    echo "   Réponse targets: $targets_body"
    
    if [ "$targets_code" = "200" ] && echo "$targets_body" | grep -q "$target_url"; then
        echo "   ⚠️  Target '$target_url' existe déjà dans '$upstream_name', ignoré"
    else
        echo "   ➕ Ajout du target '$target_url' à l'upstream '$upstream_name'"
        local add_response=$(curl -s -w "%{http_code}" -X POST "http://kong:8001/upstreams/$upstream_name/targets" \
            --data "target=$target_url" \
            --data "weight=$weight")
        local add_code="${add_response: -3}"
        local add_body="${add_response%???}"
        
        echo "   Code ajout: $add_code"
        echo "   Réponse ajout: $add_body"
        
        if [ "$add_code" = "201" ] || [ "$add_code" = "200" ]; then
            echo "   ✅ Target '$target_url' ajouté"
        else
            echo "   ❌ Erreur ajout target '$target_url' (code: $add_code)"
            echo "   Réponse: $add_body"
        fi
    fi
}

# Fonction pour créer un service s'il n'existe pas
create_service_if_not_exists() {
    local service_name=$1
    local service_url=$2
    
    echo "🔍 Vérification du service '$service_name'..."
    
    # Vérifier si le service existe déjà avec debug
    local check_response=$(curl -s -w "%{http_code}" "http://kong:8001/services/$service_name")
    local http_code="${check_response: -3}"
    local response_body="${check_response%???}"
    
    echo "   Code HTTP: $http_code"
    echo "   Réponse: $response_body"
    
    if [ "$http_code" = "200" ]; then
        echo "   ⚠️  Service '$service_name' existe déjà, ignoré"
    else
        echo "   ➕ Création du service '$service_name' avec URL '$service_url'"
        local create_response=$(curl -s -w "%{http_code}" -X POST http://kong:8001/services/ \
            --data "name=$service_name" \
            --data "url=$service_url")
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Service '$service_name' créé"
        else
            echo "   ❌ Erreur création service '$service_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

# Fonction pour créer une route si elle n'existe pas
create_route_if_not_exists() {
    local service_name=$1
    local route_name=$2
    local route_path=$3

    echo "🔍 Vérification de la route '$route_name'..."
    
    # Vérifier si la route existe déjà
    local check_response=$(curl -s -w "%{http_code}" "http://kong:8001/routes/$route_name")
    local http_code="${check_response: -3}"
    local response_body="${check_response%???}"
    
    echo "   Code HTTP: $http_code"
    echo "   Réponse: $response_body"
    
    if [ "$http_code" = "200" ]; then
        echo "   ⚠️  Route '$route_name' existe déjà, ignorée"
    else
        echo "   ➕ Création de la route '$route_name' -> '$route_path' pour service '$service_name'"
        local create_response=$(curl -s -w "%{http_code}" -X POST "http://kong:8001/services/$service_name/routes" \
            --data "name=$route_name" \
            --data "paths[]=$route_path")
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Route '$route_name' créée"
        else
            echo "   ❌ Erreur création route '$route_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

# Fonction pour créer un plugin s'il n'existe pas
create_plugin_if_not_exists() {
    local plugin_name=$1
    local plugin_config=$2
    
    echo "🔍 Vérification du plugin '$plugin_name'..."
    
    # Vérifier si le plugin existe déjà (recherche par nom)
    local plugins_response=$(curl -s -w "%{http_code}" "http://kong:8001/plugins/")
    local plugins_code="${plugins_response: -3}"
    local plugins_body="${plugins_response%???}"
    
    echo "   Code plugins: $plugins_code"
    echo "   Réponse plugins: $plugins_body"
    
    if [ "$plugins_code" = "200" ] && echo "$plugins_body" | grep -q "\"name\":\"$plugin_name\""; then
        echo "   ⚠️  Plugin '$plugin_name' existe déjà, ignoré"
    else
        echo "   ➕ Activation du plugin '$plugin_name'"
        local create_response=$(curl -s -w "%{http_code}" -X POST http://kong:8001/plugins/ \
            --data "name=$plugin_name" \
            $plugin_config)
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Plugin '$plugin_name' activé"
        else
            echo "   ❌ Erreur activation plugin '$plugin_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

# Fonction pour créer un consommateur s'il n'existe pas
create_consumer_if_not_exists() {
    local consumer_name=$1
    local custom_id=$2
    
    echo "🔍 Vérification du consommateur '$consumer_name'..."
    
    # Vérifier si le consommateur existe déjà
    local check_response=$(curl -s -w "%{http_code}" "http://kong:8001/consumers/$consumer_name")
    local http_code="${check_response: -3}"
    local response_body="${check_response%???}"
    
    echo "   Code HTTP: $http_code"
    echo "   Réponse: $response_body"
    
    if [ "$http_code" = "200" ]; then
        echo "   ⚠️  Consommateur '$consumer_name' existe déjà, ignoré"
    else
        echo "   ➕ Création du consommateur '$consumer_name'"
        local create_response=$(curl -s -w "%{http_code}" -X POST http://kong:8001/consumers/ \
            --data "username=$consumer_name" \
            --data "custom_id=$custom_id")
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Consommateur '$consumer_name' créé"
        else
            echo "   ❌ Erreur création consommateur '$consumer_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

# Fonction pour créer une clé API s'il n'existe pas
create_api_key_if_not_exists() {
    local consumer_name=$1
    local api_key=$2
    
    echo "🔍 Vérification de la clé API pour '$consumer_name'..."
    
    # Vérifier si la clé existe déjà pour ce consommateur
    local keys_response=$(curl -s -w "%{http_code}" "http://kong:8001/consumers/$consumer_name/key-auth")
    local keys_code="${keys_response: -3}"
    local keys_body="${keys_response%???}"
    
    echo "   Code clés: $keys_code"
    echo "   Réponse clés: $keys_body"
    
    if [ "$keys_code" = "200" ] && echo "$keys_body" | grep -q "$api_key"; then
        echo "   ⚠️  Clé API '$api_key' existe déjà pour '$consumer_name', ignorée"
    else
        echo "   ➕ Création de la clé API pour '$consumer_name'"
        local create_response=$(curl -s -w "%{http_code}" -X POST "http://kong:8001/consumers/$consumer_name/key-auth" \
            --data "key=$api_key")
        local create_code="${create_response: -3}"
        local create_body="${create_response%???}"
        
        echo "   Code création: $create_code"
        echo "   Réponse création: $create_body"
        
        if [ "$create_code" = "201" ] || [ "$create_code" = "200" ]; then
            echo "   ✅ Clé API créée pour '$consumer_name'"
        else
            echo "   ❌ Erreur création clé API pour '$consumer_name' (code: $create_code)"
            echo "   Réponse: $create_body"
        fi
    fi
}

echo "⚖️  Configuration du Load Balancing..."

# Créer l'upstream pour le service catalogue avec round-robin
create_upstream_if_not_exists "catalogue-upstream" "round-robin"

# Ajouter les targets (instances) à l'upstream
create_target_if_not_exists "catalogue-upstream" "catalogue-service-1:8000" "100"
create_target_if_not_exists "catalogue-upstream" "catalogue-service-2:8000" "100"
create_target_if_not_exists "catalogue-upstream" "catalogue-service-3:8000" "100"

echo "📦 Configuration des services..."

# Créer les services (catalogue utilise l'upstream)
create_service_if_not_exists "catalogue-service" "http://catalogue-upstream"
create_service_if_not_exists "inventaire-service" "http://inventaire-service:8000"
create_service_if_not_exists "commandes-service" "http://commandes-service:8000"
create_service_if_not_exists "supply-chain-service" "http://supply-chain-service:8000"
create_service_if_not_exists "ecommerce-service" "http://ecommerce-service:8005"

# === Configuration CORS sur chaque service ===
echo "🔒 Configuration CORS sur les services..."
for service in catalogue-service inventaire-service commandes-service supply-chain-service ecommerce-service; do
  echo "   ➕ Ajout du plugin CORS sur $service"
  curl -s -X POST http://localhost:8081/services/$service/plugins \
    --data "name=cors" \
    --data "config.origins=*" \
    --data "config.methods=GET,POST,PUT,DELETE,OPTIONS" \
    --data "config.headers=Accept,Authorization,Content-Type,X-API-Key" \
    --data "config.credentials=true" > /dev/null

done

echo "🛤️  Configuration des routes..."

# Créer les routes
create_route_if_not_exists "catalogue-service" "catalogue-route" "/api/catalogue"
create_route_if_not_exists "inventaire-service" "inventaire-route" "/api/inventaire"
create_route_if_not_exists "commandes-service" "commandes-route" "/api/commandes"
create_route_if_not_exists "supply-chain-service" "supply-chain-route" "/api/supply-chain"
create_route_if_not_exists "ecommerce-service" "ecommerce-route" "/api/ecommerce"

echo "🔌 Configuration des plugins..."

# Créer les plugins (fonctionnalités avancées)
create_plugin_if_not_exists "key-auth" '--data "config.key_names=X-API-Key"'
create_plugin_if_not_exists "file-log" '--data "config.path=/tmp/kong-access.log"'
create_plugin_if_not_exists "prometheus" ''

echo "👤 Configuration des consommateurs et clés API..."

# Créer le consommateur et sa clé API
create_consumer_if_not_exists "magasin-app" "magasin-frontend"
create_api_key_if_not_exists "magasin-app" "magasin-secret-key-2025"

echo "📊 Résumé de la configuration Kong:"
echo "   Upstreams: $(curl -s http://kong:8001/upstreams/ | jq '.data | length') configurés"
echo "   Services: $(curl -s http://kong:8001/services/ | jq '.data | length') configurés"
echo "   Routes: $(curl -s http://kong:8001/routes/ | jq '.data | length') configurées"
echo "   Plugins: $(curl -s http://kong:8001/plugins/ | jq '.data | length') activés"
echo "   Consommateurs: $(curl -s http://kong:8001/consumers/ | jq '.data | length') créés"

echo ""
echo "⚖️  Configuration Load Balancing:"
echo "   Upstream: catalogue-upstream (round-robin)"
echo "   Targets: $(curl -s http://kong:8001/upstreams/catalogue-upstream/targets | jq '.data | length') instances"

echo ""
echo "🔑 Clé API pour ton application:"
echo "   Header: X-API-Key: magasin-secret-key-2025"
echo ""
echo "📝 Test de l'API Gateway:"
echo "   Sans clé: curl http://localhost:8080/api/catalogue/"
echo "   Avec clé: curl -H 'X-API-Key: magasin-secret-key-2025' http://localhost:8080/api/catalogue/"
echo ""
echo "🧪 Test Load Balancing:"
echo "   for i in {1..6}; do curl -H 'X-API-Key: magasin-secret-key-2025' http://localhost:8080/api/catalogue/; echo; done"

echo "🎉 Configuration Kong avec Load Balancing terminée !" 