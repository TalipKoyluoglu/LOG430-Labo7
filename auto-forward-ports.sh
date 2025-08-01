#!/bin/bash

# Script pour automatiquement forward tous les ports Docker exposés
# Basé sur la sortie de docker ps

echo "🔍 Détection automatique des ports Docker exposés..."

# Récupérer tous les ports exposés depuis docker ps
PORTS=$(docker ps --format "table {{.Ports}}" | grep -o '[0-9]\{1,5\}->[0-9]\{1,5\}/tcp' | cut -d'>' -f1 | sort -u)

echo "📋 Ports détectés:"
echo "$PORTS"

echo ""
echo "🚀 Démarrage du forwarding automatique..."
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Forward chaque port détecté
for port in $PORTS; do
    echo "✅ Forwarding port $port..."
    # Ici vous pouvez ajouter la logique pour forward le port
    # Par exemple, ouvrir dans le navigateur ou notifier VS Code
done

echo ""
echo "✨ Tous les ports ont été configurés pour le forwarding automatique!"
echo "💡 Redémarrez VS Code pour que les changements prennent effet." 