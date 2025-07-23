#!/bin/bash

# Script pour afficher les logs Kong
# Usage: ./scripts/view-kong-logs.sh [option]

echo "📋 Logs Kong API Gateway"
echo "=========================="

case "${1:-realtime}" in
    "access")
        echo "📊 Logs d'accès Kong:"
        docker exec log430-labo5_kong_1 cat /tmp/kong-access.log 2>/dev/null || echo "❌ Aucun log d'accès trouvé"
        ;;
    "general")
        echo "📝 Logs généraux Kong:"
        docker exec log430-labo5_kong_1 cat /tmp/kong.log 2>/dev/null || echo "❌ Aucun log général trouvé"
        ;;
    "docker")
        echo "🐳 Logs Docker Kong:"
        docker logs log430-labo5_kong_1 --tail 50
        ;;
    "realtime")
        echo "🔍 Logs en temps réel (Ctrl+C pour arrêter):"
        docker logs -f log430-labo5_kong_1
        ;;
    "tail")
        echo "📊 Dernières requêtes (Ctrl+C pour arrêter):"
        docker exec log430-labo5_kong_1 tail -f /tmp/kong-access.log 2>/dev/null || echo "❌ Aucun log d'accès trouvé"
        ;;
    *)
        echo "Usage: $0 [option]"
        echo "Options:"
        echo "  access    - Afficher les logs d'accès"
        echo "  general   - Afficher les logs généraux"
        echo "  docker    - Afficher les logs Docker"
        echo "  realtime  - Logs en temps réel (défaut)"
        echo "  tail      - Dernières requêtes en temps réel"
        ;;
esac 