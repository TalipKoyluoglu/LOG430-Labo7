FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 8005

# Variables d'environnement
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PYTHONPATH=/app

# Script de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"] 