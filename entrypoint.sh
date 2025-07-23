#!/bin/sh

echo "=== Démarrage Frontend Django Orchestrateur ==="

echo "Applying minimal Django migrations (sessions, auth, etc.)..."
python manage.py migrate

echo "Django frontend ready - starting server..."
echo "Mode: Orchestrateur HTTP vers microservices via Kong"
exec python manage.py runserver 0.0.0.0:8000
