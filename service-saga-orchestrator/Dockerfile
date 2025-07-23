FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances Python
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port 8009 pour le service saga orchestrator
EXPOSE 8009

# Variables d'environnement par défaut
ENV DJANGO_SETTINGS_MODULE=saga_service.settings
ENV PYTHONPATH=/app

# Script de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8009"] 