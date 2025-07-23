# Étape 1 : Utiliser une image officielle Python plus complète
FROM python:3.12

# Étape 2 : Créer les répertoires nécessaires et définir le répertoire de travail
RUN mkdir -p /tmp /var/tmp /usr/tmp
WORKDIR /app
ENV PYTHONPATH=/app
ENV TMPDIR=/tmp

# Étape 3 : Copier les fichiers nécessaires
COPY requirements.txt .

# Étape 4 : Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt
# Étape 5 : Copier le projet complet
COPY . .
RUN chmod +x /app/entrypoint.sh

# Étape 6 : Définir la variable d'environnement Django (optionnel si non géré dans .env)
# ENV DJANGO_SETTINGS_MODULE=magasin.settings

# Étape 7 : Exposer le port utilisé par runserver
EXPOSE 8000

# Étape 8 : Commande de lancement (à override par docker-compose si besoin)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
