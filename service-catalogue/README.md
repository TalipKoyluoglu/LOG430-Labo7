# Service Produits

Service microservices pour la gestion des produits dans l'architecture e-commerce.

## 🏗️ Architecture

- **Framework** : Django 5.2.2 + Django REST Framework
- **Base de données** : PostgreSQL
- **Documentation API** : Swagger/OpenAPI
- **Port** : 8001 (externe) / 8000 (interne)

## 📋 Fonctionnalités

### Endpoints API

- `GET /api/v1/products/` - Liste des produits
- `POST /api/v1/products/` - Créer un produit
- `GET /api/v1/products/{uuid}/` - Détails d'un produit
- `PUT /api/v1/products/{uuid}/` - Modifier un produit
- `DELETE /api/v1/products/{uuid}/` - Supprimer un produit
- `GET /api/v1/products/categories/` - Liste des catégories

### Paramètres de requête

- `?categorie=Informatique` - Filtrer par catégorie
- `?search=clavier` - Rechercher par nom/description

## 🚀 Démarrage rapide

### Avec Docker Compose

```bash
cd service-produits
docker-compose up --build -d
```

### Accès

- **API Documentation** : http://localhost:8001/swagger/
- **API Base URL** : http://localhost:8001/api/v1/

## 📊 Modèle de données

```python
class Produit(models.Model):
    id = models.UUIDField(primary_key=True)  # UUID unique
    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_stock = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 🔧 Configuration

### Variables d'environnement

- `POSTGRES_DB` : Nom de la base (défaut: produits_db)
- `POSTGRES_USER` : Utilisateur DB (défaut: produits_user)
- `POSTGRES_PASSWORD` : Mot de passe DB (défaut: produits_pass)
- `POSTGRES_HOST` : Host DB (défaut: localhost)
- `POSTGRES_PORT` : Port DB (défaut: 5432)

## 📝 Données initiales

Le service charge automatiquement 5 produits de test :
- Clavier mécanique (Informatique)
- Souris optique (Informatique)
- Café Premium Bio (Boissons)
- Écouteurs Bluetooth (Informatique)
- Chocolat Noir 70% (Confiserie)

## 🔗 Communication avec autres services

Ce service sera appelé par :
- **Service Stock** : Pour vérifier l'existence des produits
- **Service Ventes** : Pour récupérer les infos produits
- **Service Dashboard** : Pour les statistiques produits

## 🧪 Tests

```bash
# Tests unitaires
python manage.py test

# Tests avec couverture
coverage run --source='.' manage.py test
coverage report
``` 