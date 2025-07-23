#!/bin/bash

# Script automatisé de test de tolérance aux pannes avec load balancer (NGINX)
# - Lance un test de charge k6
# - Arrête une instance app en cours de test
# - Attend, puis redémarre l'instance
# - Observe l'impact sur la continuité du service

# Paramètres personnalisables
K6_SCRIPT="scripts/load_test_baseline.js"   # Chemin du script k6
INSTANCE_TO_KILL="app_2"             # Nom du conteneur à arrêter (adapter si besoin)
DURATION_BEFORE_KILL=45                     # Secondes avant d'arrêter l'instance
DURATION_AFTER_KILL=90                     # Secondes à attendre après l'arrêt avant de relancer

# 1. Démarrer le test de charge en arrière-plan
echo "[INFO] Démarrage du test de charge k6..."
k6 run $K6_SCRIPT &
K6_PID=$!

# 2. Attendre avant de simuler la panne
sleep $DURATION_BEFORE_KILL

echo "[INFO] Arrêt de l'instance $INSTANCE_TO_KILL pour simuler une panne..."
docker stop $INSTANCE_TO_KILL

# 3. Attendre la fin du test de charge (ou une période donnée)
sleep $DURATION_AFTER_KILL

echo "[INFO] Redémarrage de l'instance $INSTANCE_TO_KILL..."
docker start $INSTANCE_TO_KILL

# 4. Attendre la fin du test de charge
wait $K6_PID

echo "[INFO] Test de tolérance aux pannes terminé. Vérifiez les métriques k6, Grafana et les logs NGINX." 