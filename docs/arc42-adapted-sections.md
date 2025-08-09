# Sections Adaptées selon vos Vrais Diagrammes UML

## 5.2 Vue Déploiement (selon vue-deploiement.puml)

![Vue deploiement](./UML/vue-deploiement.png)

#### **Observabilité**
- **Grafana** : Port 3000 - Dashboards saga orchestrée vs chorégraphiée
- **Prometheus** : Port 9090 - Collecte métriques de tous services + workers

#### **Frontend Application**
- **client-app** avec NGINX (Port 80) : Proxy vers Django App (Port 8000 interne)
- **Django App** : Frontend orchestrateur avec vues spécialisées

#### **API Gateway**
- **Kong** : Port 8080 (proxy) + 8081 (admin)
- **Load Balancing** : Catalogue service (3 instances)
- **Routage** : Routes dédiées vers chaque microservice

#### **Infrastructure Événementielle (Lab7)**
- **Redis Streams** : Port 6379 - Event Bus + persistance événements
- **Event Store (Flask)** : Port 7010 - API replay + CQRS read models

#### **Microservices (Ports 8001-8005)**
- **catalogue-service-*** : 3 instances load balancées
  - Catalogue 1 : Port 8001
  - Catalogue 2 : Port 8006  
  - Catalogue 3 : Port 8007
- **inventaire-service** : Port 8002
- **commandes-service** : Port 8003
- **supply-chain-service** : Port 8004
- **ecommerce-service** : Port 8005

#### **Service Saga Orchestrateur (Lab6)**
- **service-saga-orchestrator** : Port 8009 (**correction du port**)

#### **Workers Chorégraphiés (Lab7)**
- **notification-worker** : Port 9100
- **audit-worker** : Port 9101
- **stock-reservation-worker** : Port 9102
- **order-creation-worker** : Port 9103
- **stock-compensation-worker** : Port 9104
- **cqrs-projection-worker** : Port 9105

#### **Bases de Données (Ports 5433-5438)**
- **Kong DB** : Port 5433
- **Catalogue DB** : Port 5434
- **Inventaire DB** : Port 5435
- **Commandes DB** : Port 5436
- **SupplyChain DB** : Port 5437
- **Ecommerce DB** : Port 5438

---

## 5.3 Vue Logique (selon vue-logique.puml)

![Vue logique](./UML/vue-logique.png)

### **Bounded Contexts DDD (5 contextes métier)**

#### **Bounded Context: Catalogue Management (service-catalogue:8001)**

**Domain Layer**
```
Produit (Entity): id, nom, prix, reference_sku, categorie, est_actif
  + archiver_produit(), modifier_prix(nouveau_prix), valider_donnees(), est_disponible_vente()
Categorie (Entity): id, nom, description, parent_id
  + ajouter_sous_categorie(), valider_hierarchie()
NomProduit (VO): valeur + valider_longueur(), normaliser()
PrixMonetaire (VO): montant, devise + valider_positif(), formater_affichage()
ReferenceSKU (VO): code + valider_unicite(), generer_code()
```

**Application Layer**
```
RechercherProduitsUseCase: execute(criteres) - appliquer_filtres(), trier_par_pertinence()
AjouterProduitUseCase: execute(donnees_produit) - valider_donnees_metier(), verifier_unicite_sku()
ModifierPrixUseCase: execute(produit_id, nouveau_prix) - valider_autorisation(), journaliser_changement()
```

#### **Bounded Context: Inventory Management (service-inventaire:8002)**

**Domain Layer**
```
StockCentral (Entity): produit_id, quantite, seuil_alerte
  + diminuer_stock(quantite), augmenter_stock(quantite), est_disponible(quantite), doit_reapprovisionner()
StockLocal (Entity): produit_id, magasin_id, quantite, derniere_maj
  + transferer_vers_local(quantite), vendre_produit(quantite), calculer_rotation()
DemandeReapprovisionnement (Entity): id, produit_id, magasin_id, quantite, statut, date_creation
  + approuver(), rejeter(motif), peut_etre_validee()
Quantite (VO): valeur + valider_positive(), est_importante()
```

#### **Bounded Context: Sales Management (service-commandes:8003)**

**Domain Layer**
```
Vente (Entity): id, magasin_id, client_id, statut, total, date_vente
  + peut_etre_annulee(), calculer_total(), ajouter_ligne_vente(), annuler_avec_motif()
Magasin (Entity): id, nom, adresse
  + peut_vendre(produit_id, quantite, stock), calculer_chiffre_affaires(), obtenir_indicateurs()
CommandeVente (VO): produit_id, quantite, prix_unitaire
  + valider_commande(), calculer_sous_total()
StatutVente (VO): valeur + est_finale(), peut_transitionner_vers()
```

#### **Bounded Context: Supply Chain Management (service-supply-chain:8004)**

**Domain Layer**
```
WorkflowValidation (Entity): demande_id, etapes_completees, statut_workflow, rollback_effectue
  + executer_etape(nom_etape), rollback_si_echec(), est_workflow_complet()
MotifRejet (VO): texte, categorie + valider_longueur_minimale(), nettoyer_contenu()
```

**Application Layer**
```
ValiderDemandeUseCase: execute(demande_id)
  - workflow_3_etapes(), rollback_automatique(), journaliser_operations()
```

#### **Bounded Context: E-commerce Management (service-ecommerce:8005)**

**Domain Layer**
```
Client (Entity): id, prenom, nom, email, adresse
  + peut_commander(), valider_donnees(), creer_panier()
Panier (Entity): client_id, produits, statut
  + ajouter_produit(produit_id, quantite), vider_panier(), calculer_total(), est_pret_checkout()
ProcessusCheckout (Entity): panier_id, adresse_livraison, statut_checkout
  + valider_prerequis(), finaliser_commande(), calculer_frais_livraison()
AdresseLivraison (VO): rue, ville, code_postal + valider_format(), normaliser_adresse()
```

### **Event Bus: Redis Streams (Lab7)**

**Topic Principal** : `ecommerce.checkout.events`

**Types d'Événements (8 types définis)** :
```
CheckoutInitiated, StockReserved, OrderCreated, CheckoutSucceeded
StockReservationFailed, OrderCreationFailed, StockReleased, CheckoutFailed
```

**Consumer Groups** :
- `choreo-reservation` → stock_reservation_worker
- `choreo-order` → order_creation_worker  
- `choreo-compensation` → stock_compensation_worker
- `checkout-notification` → notification_worker
- `checkout-audit` → audit_worker
- `checkout-cqrs` → cqrs_projection_worker

---

## 5.4 Vue Cas d'Utilisation (selon vue-cas-utilisation.puml)

![Vue cas d'utilisation](./UML/vue-cas-utilisation.png)

### **Acteurs et Hiérarchie**
```
Client Web
Employe Magasin
Gestionnaire (extends Employe Magasin)
```

### **Use Cases par Domaine**

#### **Domaine Catalogue**
- **UC01** : Rechercher produits
- **UC02** : Consulter details produit (includes UC01)
- **UC03** : Gerer catalogue (includes UC01)

#### **Domaine Inventaire**
- **UC04** : Consulter stocks
- **UC05** : Creer demande reappro
- **UC06** : Transferer stock (includes UC05)
- **UC07** : Gerer alertes stock (includes UC04)

#### **Domaine Commandes**
- **UC08** : Enregistrer vente
- **UC09** : Traiter paiement (includes UC08)
- **UC10** : Generer rapports
- **UC11** : Analyser performances (includes UC10)
- **UC20** : Annuler commande

#### **Domaine Supply Chain**
- **UC12** : Valider demandes reappro
- **UC14** : Gerer workflow validation (includes UC12, UC19)
- **UC19** : Rejeter demandes reappro

#### **Domaine E-commerce**
- **UC15** : Creer compte client
- **UC16** : Ajouter au panier
- **UC17** : Finaliser commande (orchestrée) - includes UC16
- **UC18** : Gerer profil client (includes UC15)
- **UC21** : Checkout chorégraphié (Pub/Sub) - includes UC16

### **Relations Acteurs → Use Cases**

**Client Web** : UC15, UC16, UC17, UC21 (E-commerce)
**Employe Magasin** : UC04, UC05, UC08, UC20 (Inventaire + Commandes)
**Gestionnaire** : UC03, UC10, UC11, UC14 (+ droits employé)

### **Relations Inter-domaines Critiques**
- UC08 → UC04 : Reduction stock
- UC17 → UC04 : Verification stock
- UC17 → UC08 : Creation commande
- UC21 → UC04 : Reserve/Release stock (events)
- UC21 → UC08 : Creer commande (events)
- UC12 → UC06 : Execution transfert
- UC20 → UC06 : Remet le stock

---

## 6.1-6.2 Processus Saga (selon scenario-checkout-ecommerce.puml + saga-state-machine.puml)

![Séquence checkout comparatif](./UML/scenario-checkout-ecommerce.png)
![Machine d'état saga](./UML/saga-state-machine.png)

### **Comparaison Lab6 vs Lab7**

#### **Lab6 - Saga Orchestrée (Synchrone)**

**Acteurs** : Client Web, Frontend E-commerce, Kong Gateway, service-ecommerce, service-inventaire, service-commandes

**Séquence** :
1. Client → Frontend : `POST /checkout` (synchrone)
2. Frontend → Kong : `/api/ecommerce/commandes/clients/{id}/checkout/`
3. Kong → EcommerceService : orchestré
4. EcommerceService → Inventaire : vérifier puis diminuer stock
5. EcommerceService → Commandes : créer vente
6. EcommerceService → Client : `201/400` selon succès

#### **Lab7 - Saga Chorégraphiée (Asynchrone)**

**Acteurs** : Client Web, Frontend E-commerce, Kong Gateway, service-ecommerce, Redis Streams, Workers, Services

**Séquence** :
1. Client → Frontend : `POST /checkout/choreo` (async)
2. Frontend → Kong : `/api/ecommerce/.../checkout/choreo/`
3. Kong → EcommerceService : `202 Accepted` + checkout_id
4. EcommerceService → Bus : publish CheckoutInitiated
5. WRes → Bus : consume CheckoutInitiated
6. WRes → Inventaire : diminuer-stock
7. WRes → Bus : publish StockReserved | StockReservationFailed
8. WOrd → Bus : consume StockReserved
9. WOrd → Commandes : enregistrer-vente
10. WOrd → Bus : publish OrderCreated, CheckoutSucceeded | OrderCreationFailed
11. WComp → Bus : consume OrderCreationFailed | StockReservationFailed
12. WComp → Inventaire : augmenter-stock
13. WComp → Bus : publish StockReleased, CheckoutFailed

### **Machine d'État Saga Orchestrée**

**États Principaux** :
```
EN_ATTENTE → VERIFICATION_STOCK → STOCK_VERIFIE → RESERVATION_STOCK → 
STOCK_RESERVE → CREATION_COMMANDE → COMMANDE_CREEE → SAGA_TERMINEE
```

**États d'Échec** :
- ECHEC_STOCK_INSUFFISANT → SAGA_ANNULEE (aucune compensation)
- ECHEC_RESERVATION_STOCK → SAGA_ANNULEE (aucune compensation) 
- ECHEC_CREATION_COMMANDE → COMPENSATION_EN_COURS → SAGA_ANNULEE

**Transitions Critiques** :
- ECHEC_CREATION_COMMANDE → COMPENSATION_DEMANDEE → libération stock
- COMPENSATION_EN_COURS → POST /api/inventaire/augmenter-stock/
- COMPENSATION_TERMINEE → SAGA_ANNULEE
