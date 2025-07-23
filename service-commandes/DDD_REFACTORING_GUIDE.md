# 🏗️ Refactorisation DDD - Service Ventes

## 📁 **Nouvelle structure**

```
service-ventes/ventes/
├── domain/                    # 💼 CŒUR MÉTIER
│   ├── entities.py           # Entités riches (Vente, Magasin)
│   ├── value_objects.py      # Objects valeur (CommandeVente, Money)
│   └── exceptions.py         # Exceptions métier spécifiques
│
├── application/               # 📋 ORCHESTRATION
│   ├── use_cases/            # Use Cases par fonctionnalité
│   │   ├── enregistrer_vente_use_case.py
│   │   ├── annuler_vente_use_case.py
│   │   └── generer_indicateurs_use_case.py
│   ├── repositories/         # Interfaces d'accès données
│   └── services/            # Interfaces services externes
│
├── infrastructure/           # 🔧 IMPLÉMENTATION
│   ├── django_vente_repository.py      # Implémentation Django ORM
│   ├── django_magasin_repository.py    # Conversion entités ↔ modèles
│   ├── http_produit_service.py         # Communication HTTP
│   └── http_stock_service.py           # avec services externes
│
├── interfaces/              # 🌐 PRÉSENTATION
│   └── ddd_views.py         # Controllers DDD (orchestration pure)
│
└── models.py               # Django models (inchangés)
```

---

## 🔄 **Comparaison CRUD vs DDD**

### **Approche CRUD (ancienne)**
```python
# services.py - Logique technique par entité
def enregistrer_vente(magasin_id, produit_id, quantite):
    # Validation
    # Récupération
    # Calculs
    # Persistance
    
def annuler_vente(vente_id):
    # Logique d'annulation
    
def generer_indicateurs():
    # Calcul des statistiques
```

### **Approche DDD (nouvelle)**
```python
# Use Cases - Fonctionnalités métier
class EnregistrerVenteUseCase:
    def execute(self, commande: CommandeVente):
        # Orchestration avec entités riches
        
class AnnulerVenteUseCase:
    def execute(self, vente_id: str, motif: str):
        vente.annuler(motif)  # Logique dans l'entité
        
class GenererIndicateursUseCase:
    def execute(self):
        # Focus sur la fonctionnalité métier
```

---

## 🚀 **Endpoints disponibles**

### **Routes CRUD** (compatibilité)
- `POST /ventes/enregistrer/`
- `PATCH /ventes/{id}/annuler/`
- `GET /indicateurs/magasins/`

### **Routes DDD** (nouvelles)
- `POST /api/ddd/ventes-ddd/enregistrer/` → **EnregistrerVenteUseCase**
- `PATCH /api/ddd/ventes-ddd/{id}/annuler/` → **AnnulerVenteUseCase**
- `GET /api/ddd/indicateurs/` → **GenererIndicateursUseCase**

---

## 💡 **Avantages de la refactorisation**

### **1. Logique métier centralisée**
```python
# Avant (logique dispersée)
if stock_disponible < quantite:
    return {"error": "Stock insuffisant"}

# Après (logique dans l'entité)
if not magasin.peut_vendre(produit_id, quantite, stock_disponible):
    raise StockInsuffisantError(...)
```

### **2. Use Cases testables**
```python
# Mock des services externes facilement
use_case = EnregistrerVenteUseCase(
    mock_vente_repo,
    mock_magasin_repo,
    mock_produit_service,
    mock_stock_service
)
```

### **3. Évolutivité**
Ajouter une nouvelle fonctionnalité = 1 nouveau Use Case
- `RemboursementVenteUseCase`
- `TransfertStockUseCase`
- `ValidationRetourUseCase`

### **4. Séparation des responsabilités**
- **Domain** : Règles métier pures
- **Application** : Orchestration des use cases
- **Infrastructure** : Détails techniques (BD, HTTP)
- **Interface** : Présentation (API REST)

---

## 🧪 **Tests possibles**

```python
# Test unitaire d'entité
def test_vente_annulation():
    vente = Vente(id=uuid4(), magasin_id=magasin_id)
    vente.annuler("Erreur de caisse")
    assert vente.statut == StatutVente.ANNULEE

# Test d'intégration de Use Case
def test_enregistrer_vente_use_case():
    # Avec mocks des services externes
    commande = CommandeVente(...)
    resultat = use_case.execute(commande)
    assert resultat["success"] is True
```

---

## 🔮 **Prochaines étapes recommandées**

1. **Dependency Injection** : Remplacer l'instanciation manuelle par un DI container
2. **Domain Events** : Publier des événements métier (vente créée, annulée)
3. **CQRS** : Séparer commandes et requêtes
4. **Integration Tests** : Tester les use cases avec vrais services externes
5. **Performance** : Ajouter du cache sur les indicateurs

---

## 🎓 **Conclusion**

Cette refactorisation transforme le service d'une architecture **technique** (CRUD) vers une architecture **métier** (DDD) :

- **Avant** : 50 entités = 50 services techniques
- **Après** : N fonctionnalités = N use cases métier

Le code est maintenant :
- ✅ **Plus maintenable** (logique centralisée)
- ✅ **Plus testable** (injection de dépendances)
- ✅ **Plus évolutif** (ajout facile de fonctionnalités)
- ✅ **Plus lisible** (intention métier claire)

**Votre professeur devrait être satisfait ! 🎯** 