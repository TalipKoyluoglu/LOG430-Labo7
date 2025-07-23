# Tests Microservices DDD - Architecture Kong Gateway

Ce répertoire contient les tests d'intégration et End-to-End pour l'architecture microservices DDD avec Kong API Gateway.

## 🏗️ Architecture Testée

```
Frontend Django → Kong Gateway → 5 Microservices DDD
                     ↓
    3 instances service-catalogue (load balancé)
    + service-inventaire, service-commandes, 
      service-supply-chain, service-ecommerce
```

## 📁 Organisation des Tests

```
tests/
├── integration/                   # Tests inter-services via Kong
│   ├── conftest.py               # Configuration Kong Gateway
│   ├── test_workflow_ecommerce.py # Workflow checkout complet
│   └── test_kong_load_balancing.py # Load balancing 3 instances
├── e2e/                          # Tests via frontend Django
│   ├── conftest.py               # Configuration Django client
│   └── test_frontend_orchestration.py # Orchestration frontend
└── README.md                     # Ce fichier
```

## 🚀 Types de Tests

### 1. Tests d'Intégration (`tests/integration/`)

**Description** : Tests avec microservices réels via Kong Gateway  
**Environnement** : Docker Compose complet  
**Durée** : ~5-10 minutes  

**Tests inclus :**
- ✅ Workflow e-commerce complet (client → panier → checkout → commande)
- ✅ Communication inter-services HTTP
- ✅ Load balancing Kong sur 3 instances catalogue
- ✅ Health checks et failover automatique
- ✅ Performance sous charge modérée

### 2. Tests End-to-End (`tests/e2e/`)

**Description** : Tests via interface Django avec mocking des microservices  
**Environnement** : Django + PostgreSQL + Redis  
**Durée** : ~2-3 minutes  

**Tests inclus :**
- ✅ Orchestration frontend → clients HTTP → microservices
- ✅ Workflows utilisateur (employé, gestionnaire, client)
- ✅ Gestion d'erreurs quand services indisponibles
- ✅ Configuration clients HTTP Kong

## 🛠️ Prérequis

### Environnement Développement
```bash
# Python 3.11 + dépendances
pip install -r requirements.txt
pip install pytest pytest-django requests

# Docker + Docker Compose
docker --version
docker-compose --version

# Optionnel : k6 pour tests de charge
# Ubuntu/Debian
sudo apt-get install k6
```

### Services Requis

**Tests E2E :**
- PostgreSQL (port 5432)
- Redis (port 6379)

**Tests Intégration :**
- Environnement microservices complet
- Kong Gateway (ports 8080, 8081)
- 5 microservices + 7 bases PostgreSQL

## 🧪 Exécution des Tests

### Script Automatisé (Recommandé)

```bash
# Tests unitaires (rapides)
./scripts/run_tests.sh unit

# Tests E2E (frontend Django)
./scripts/run_tests.sh e2e

# Tests d'intégration (microservices)
./scripts/run_tests.sh integration

# Tous les tests
./scripts/run_tests.sh all

# Simulation pipeline CI complète
./scripts/run_tests.sh ci

# Nettoyage
./scripts/run_tests.sh clean
```

### Exécution Manuelle

#### Tests E2E
```bash
# Démarrer PostgreSQL + Redis
docker-compose up -d db redis

# Migrations Django
python manage.py migrate

# Tests E2E
pytest tests/e2e/ -v --tb=short -m e2e
```

#### Tests d'Intégration
```bash
# Démarrer environnement complet
docker-compose up -d
sleep 60

# Configurer Kong
./scripts/setup-kong.sh
sleep 10

# Tests d'intégration
KONG_GATEWAY_URL=http://localhost:8080 \
KONG_ADMIN_URL=http://localhost:8081 \
pytest tests/integration/ -v --tb=short -m integration
```

#### Tests Spécifiques
```bash
# Test workflow e-commerce uniquement
pytest tests/integration/test_workflow_ecommerce.py::TestWorkflowEcommerce::test_workflow_ecommerce_complet -v

# Test load balancing Kong uniquement
pytest tests/integration/test_kong_load_balancing.py -v

# Test orchestration frontend uniquement
pytest tests/e2e/test_frontend_orchestration.py -v
```

## 📊 Configuration des Tests

### Markers Pytest

```ini
# pytest.ini
markers =
    integration: Tests d'intégration (services réels)
    e2e: Tests end-to-end (via Django client)
```

### Variables d'Environnement

```bash
# Configuration Kong Gateway
KONG_GATEWAY_URL=http://localhost:8080  # Proxy Kong
KONG_ADMIN_URL=http://localhost:8081    # Admin Kong

# Configuration Django
DJANGO_SETTINGS_MODULE=config.settings
PYTHONPATH=.
```

### Fixtures Principales

**Tests Intégration :**
- `kong_client` : Client HTTP avec headers Kong
- `wait_for_services` : Attente que tous les services soient prêts
- `test_client_data` : Données client e-commerce de test
- `cleanup_test_data` : Nettoyage automatique après tests

**Tests E2E :**
- `django_client` : Client Django pour tests interface
- `test_user_data` : Données utilisateur de test

## 🔍 Workflows Testés

### 1. Workflow E-commerce Complet
```
1. Créer compte client (service-ecommerce)
2. Rechercher produit (service-catalogue via Kong LB)
3. Ajouter produit au panier (service-ecommerce)
4. Checkout complet (service-ecommerce → service-commandes)
5. Vérifier commande créée (service-commandes)
6. Vérifier panier vidé (service-ecommerce)
```

### 2. Load Balancing Kong
```
1. 30 requêtes vers service-catalogue
2. Vérification distribution round-robin (10±1 par instance)
3. Health checks automatiques Kong
4. Test de failover (simulation panne instance)
```

### 3. Orchestration Frontend
```
1. Interface Django → Clients HTTP
2. Clients HTTP → Kong Gateway → Microservices
3. Gestion d'erreurs services indisponibles
4. Configuration API Keys Kong
```

## 🚨 Dépannage

### Erreurs Communes

**"Kong Gateway not ready"**
```bash
# Vérifier Kong
curl http://localhost:8080/
curl http://localhost:8081/

# Redémarrer si nécessaire
docker-compose restart kong
```

**"Service indisponible"**
```bash
# Vérifier tous les services
docker-compose ps

# Logs d'un service
docker-compose logs catalogue-service-1

# Redémarrer environnement
docker-compose down && docker-compose up -d
```

**"Tests échouent en intégration"**
```bash
# Augmenter les timeouts d'attente
# Dans conftest.py : max_retries = 60

# Vérifier la configuration Kong
./scripts/setup-kong.sh

# Tests avec plus de verbosité
pytest tests/integration/ -v -s --tb=long
```

### Logs Utiles

```bash
# Logs Kong Gateway
docker-compose logs kong

# Logs microservices
docker-compose logs catalogue-service-1
docker-compose logs ecommerce-service

# Logs base de données
docker-compose logs produits-db
```

## 🎯 Métriques de Validation

### Tests d'Intégration
- ✅ **100% taux de succès** workflow e-commerce
- ✅ **Distribution équitable** load balancing (±1 requête)
- ✅ **Latence < 500ms** P95 sous charge modérée
- ✅ **Failover < 5s** détection panne Kong

### Tests E2E
- ✅ **Interface responsive** même avec services down
- ✅ **Configuration correcte** clients HTTP Kong
- ✅ **Orchestration fonctionnelle** frontend → microservices

## 📝 Pipeline CI/CD

Les tests sont intégrés dans `.github/workflows/ci.yml` :

1. **Phase 1** : Tests unitaires + E2E (rapides)
2. **Phase 2** : Tests d'intégration microservices
3. **Phase 3** : Tests de charge Kong (k6)
4. **Phase 4** : Build et déploiement

**Temps total pipeline** : ~15-20 minutes

## 🤝 Contribution

Pour ajouter de nouveaux tests :

1. **Tests d'intégration** : Ajouter dans `tests/integration/`
2. **Tests E2E** : Ajouter dans `tests/e2e/`
3. **Markers** : Utiliser `@pytest.mark.integration` ou `@pytest.mark.e2e`
4. **Documentation** : Mettre à jour ce README

---

**Auteur** : Talip Koyluoglu  
**Projet** : LOG430 Labo 5 - Architecture Microservices DDD  
**Date** : Janvier 2025 