# LOG430 – Laboratoire 5 : Architecture Microservices DDD

## Présentation
Ce laboratoire transforme une application multi-magasins monolithique en une architecture microservices basée sur les principes du Domain-Driven Design (DDD). Le système distribué met en œuvre 5 microservices autonomes avec des bounded contexts distincts, orchestrés par une API Gateway Kong et supportés par une infrastructure complète d'observabilité.

## Architecture globale

### Microservices DDD
- **service-catalogue** : Gestion des produits et du catalogue (3 instances load-balancées)
- **service-inventaire** : Gestion des stocks et demandes de réapprovisionnement  
- **service-commandes** : Gestion des ventes et rapports commerciaux
- **service-supply-chain** : Validation des processus de réapprovisionnement
- **service-ecommerce** : Interface e-commerce et processus de checkout

### Infrastructure
- **API Gateway** : Kong (routage, load balancing, authentification par clé API)
- **Frontend** : Django avec clients HTTP dédiés pour chaque microservice
- **Bases de données** : 7 instances PostgreSQL dédiées par bounded context
- **Cache** : Redis pour optimisation des performances
- **Observabilité** : Prometheus (métriques), Grafana (dashboards), logging distribué

## Bounded Contexts et Domaines

### 1. Catalogue (service-catalogue)
- **Entités** : Produit, Catégorie, Fournisseur
- **Ports** : 8001, 8006, 8007 (load balancing)
- **Responsabilités** : CRUD produits, gestion catalogue, recherche

### 2. Inventaire (service-inventaire) 
- **Entités** : Stock, DemandeReappro, Mouvement
- **Port** : 8002
- **Responsabilités** : Suivi stocks, alertes, demandes réapprovisionnement

### 3. Commandes (service-commandes)
- **Entités** : Vente, LigneVente, Rapport
- **Port** : 8003  
- **Responsabilités** : Enregistrement ventes, rapports commerciaux

### 4. Supply Chain (service-supply-chain)
- **Entités** : ValidationReappro, ProcessusValidation
- **Port** : 8004
- **Responsabilités** : Workflow validation réapprovisionnement (3 étapes)

### 5. E-commerce (service-ecommerce)
- **Entités** : Panier, Commande, Paiement
- **Port** : 8005
- **Responsabilités** : Processus checkout e-commerce (4 phases)

## Workflows Inter-Services

### 1. Enregistrement de Vente
```
Employé → Frontend Django → CommandesClient → Kong → service-commandes → service-inventaire
```
Communication synchrone HTTP pour mise à jour immédiate des stocks.

### 2. Validation Réapprovisionnement  
```
Manager → Frontend → SupplyChainClient → Kong → service-supply-chain
```
Workflow atomique en 3 étapes : validation produit, stock, fournisseur.

### 3. Checkout E-commerce
```
Client → Frontend → EcommerceClient → service-ecommerce → service-catalogue + service-commandes
```
Processus en 4 phases : validation panier, réservation stock, paiement, confirmation.

## Résultats de Performance

| Métrique                    | Lab 4 (Monolithe) | Lab 5 (Microservices) | Amélioration |
|-----------------------------|--------------------|-----------------------|--------------|
| Latence moyenne             | 70.16ms            | 18.26ms               | -74%         |
| Latence p95                 | 4.99s              | 45ms                  | -99%         |
| Taux d'erreur               | 10.95%             | 0%                    | -100%        |
| Débit maximal               | 100 req/s          | 500+ req/s            | +400%        |
| Temps de réponse stable     | Non                | Oui                   | Stable       |

## Utilisation rapide

### Prérequis
- Docker et Docker Compose installés
- Ports 8001-8007, 8080-8081, 5432, 6379, 9090, 3000 disponibles

### Lancement de l'architecture complète
```bash
git clone https://github.com/TalipKoyluoglu/LOG430-Labo5
cd LOG430-Labo5
docker-compose up --build -d
```

### Accès aux services
- **Frontend Django** : http://localhost:8000/
- **Kong API Gateway** : http://localhost:8080/ (proxy), http://localhost:8081/ (admin)
- **Service Catalogue** : http://localhost:8001/, 8006/, 8007/ (load-balanced)
- **Service Inventaire** : http://localhost:8002/
- **Service Commandes** : http://localhost:8003/
- **Service Supply Chain** : http://localhost:8004/
- **Service E-commerce** : http://localhost:8005/
- **Prometheus** : http://localhost:9090/
- **Grafana** : http://localhost:3000/ (admin/admin)

### Tests des workflows
```bash
# Tests d'intégration Kong Gateway
python -m pytest tests/integration/test_kong_gateway.py -v

# Tests E2E orchestration frontend  
python -m pytest tests/e2e/test_frontend_orchestration.py -v

# Tests de charge
k6 run scripts/load_test_microservices.js
```

## Structure du projet
```plaintext
LOG430-Labo5/
├── services/
│   ├── service-catalogue/    # Microservice catalogue (DDD)
│   ├── service-inventaire/   # Microservice inventaire
│   ├── service-commandes/    # Microservice commandes
│   ├── service-supply-chain/ # Microservice supply chain
│   └── service-ecommerce/    # Microservice e-commerce
├── frontend-magasin/         # Django frontend avec clients HTTP
├── kong/                     # Configuration Kong Gateway
├── tests/
│   ├── integration/          # Tests Kong, workflows inter-services
│   └── e2e/                  # Tests orchestration frontend
├── docs/
│   ├── UML/                  # Diagrammes architecture (PlantUML)
│   └── arc42.md              # Documentation architecture Arc42
├── scripts/                  # Scripts de test de charge k6
├── docker-compose.yml        # Orchestration complète
└── README.md
```

## Communication Inter-Services

### Protocole HTTP Synchrone
- **Gateway** : Kong avec routage par préfixes (`/catalogue/`, `/inventaire/`, etc.)
- **Authentification** : Clés API Kong pour sécurisation
- **Load Balancing** : Round-robin automatique sur service-catalogue
- **Format** : JSON REST standardisé entre tous les services

### Clients HTTP Dédiés (Frontend)
```python
# Exemple d'utilisation
catalogue_client = CatalogueClient()
produits = catalogue_client.get_produits()

commandes_client = CommandesClient()  
commandes_client.enregistrer_vente(vente_data)
```

## Observabilité Distribuée

### Métriques Prometheus
- Latence par microservice et endpoint
- Débit de requêtes inter-services  
- Statuts de santé des services
- Métriques métier (stocks, ventes, validations)

### Dashboards Grafana
- Vue d'ensemble architecture microservices
- Performance par bounded context
- Workflows inter-services en temps réel
- Alertes sur indisponibilité services

### Logging Distribué
- Correlation IDs pour traçage inter-services
- Logs JSON structurés par service
- Centralisation pour debugging workflows

## Tests et Qualité

### Tests d'Intégration
- Communication Kong Gateway ↔ Microservices
- Workflows inter-services complets
- Load balancing et failover

### Tests End-to-End  
- Orchestration frontend Django
- Scenarios métier complets
- Validation bounded contexts

### Tests de Charge
- Performance sous charge distribué
- Scalabilité horizontale
- Resilience aux pannes

## Pipeline CI/CD
Configuration GitHub Actions pour :
- Build et tests de tous les microservices
- Tests d'intégration Kong Gateway  
- Tests E2E orchestration frontend
- Déploiement containerisé coordonné

## Documentation Architecture
- **Arc42** : [`docs/arc42.md`](docs/arc42.md) - Architecture complète
- **UML** : [`docs/UML/`](docs/UML/) - Diagrammes PlantUML (déploiement, logique, cas d'utilisation)
- **API** : Documentation Swagger par microservice

## Auteur
Projet réalisé par Talip Koyluoglu dans le cadre du cours LOG430.
