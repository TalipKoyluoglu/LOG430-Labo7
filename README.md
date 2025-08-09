# LOG430 – Labo 7: Architecture Événementielle (Pub/Sub, Event Sourcing, CQRS, Saga Chorégraphiée)

## Présentation
Ce laboratoire étend l'architecture microservices DDD des labos précédents avec une approche événementielle complète:
- Pub/Sub via Redis Streams (plusieurs abonnés)
- Event Sourcing (historique persistant + replay)
- CQRS (projections de lecture dédiées)
- Saga chorégraphiée (coordination sans orchestrateur central)
- Observabilité (Prometheus, Grafana)

Références utiles:
- Documentation d’architecture: `docs/arc42.md`
- Diagrammes UML: `docs/UML/` (déploiement, logique, cas d’utilisation, séquence, machine d’état)

## Composants ajoutés (répertoire `lab7/`)

- `common/event_bus.py` – Wrapper Redis Streams (publish/subscribe, groups)
- `common/metrics.py` – Compteurs/histogrammes Prometheus (pub/consommation/latence, succès/échec saga)
- `event_store/app.py` – API Flask d’Event Store (lecture/replay/projections CQRS)
  - `GET /api/event-store/streams/<stream>/events`
  - `GET /api/event-store/replay/checkout/<checkout_id>`
  - `GET /api/event-store/cqrs/orders-by-client/<client_id>`
- `consumers/notification_worker.py` – Abonné de notification (metrics: 9100)
- `consumers/audit_worker.py` – Abonné d’audit (metrics: 9101)
- `consumers/stock_reservation_worker.py` – Réservation stock (group: choreo-reservation, metrics: 9102)
- `consumers/order_creation_worker.py` – Création commande (group: choreo-order, metrics: 9103)
- `consumers/stock_compensation_worker.py` – Compensation stock (group: choreo-compensation, metrics: 9104)
- `consumers/cqrs_projection_worker.py` – Projection CQRS (group: checkout-cqrs, metrics: 9105)

Service e-commerce (modifié):
- Endpoint asynchrone: `POST /api/commandes/clients/{client_id}/checkout/choreo/`
- Publie: `CheckoutInitiated`, `CheckoutSucceeded`, `CheckoutFailed`

## Démarrage rapide

Prérequis: Docker et Docker Compose; ports libres: 6379 (Redis), 7010 (Event Store), 9090 (Prometheus), 3000 (Grafana), 8080/8081 (Kong), 8001-8007 (services).

Lancer toute l’architecture:
```bash
docker-compose up --build -d
```

Accès principaux:
- Kong (proxy/admin): `http://localhost:8080` / `http://localhost:8081`
- Event Store (Flask): `http://localhost:7010`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)
- Services: Catalogue `8001/8006/8007`, Inventaire `8002`, Commandes `8003`, Supply Chain `8004`, E-commerce `8005`

Workers (exposent les métriques Prometheus):
- notification (9100), audit (9101), stock-reservation (9102), order-creation (9103), stock-compensation (9104), cqrs-projection (9105)

Notes internes (réseau Docker):
- Les workers appellent Kong via `http://kong:8000` (variable `KONG_URL`)
- L’Event Store lit Redis via `REDIS_URL=redis://redis:6379/0`

## Tester le checkout chorégraphié (succès)

1) Initier un checkout (via Kong):
```bash
CLIENT_UUID=<UUID_CLIENT>
PRODUIT_UUID=<UUID_PRODUIT>

curl -s -X POST \
  http://localhost:8080/ecommerce/api/commandes/clients/$CLIENT_UUID/checkout/choreo/ \
  -H 'Content-Type: application/json' \
  -d '{
    "panier": { "lignes": [ { "produit_id": "'$PRODUIT_UUID'", "quantite": 1 } ] },
    "adresse_livraison": { "rue": "1 rue A", "ville": "MTL", "code_postal": "H1H1H1" }
  }'
# Réponse: { "accepted": true, "checkout_id": "...", "follow": "http://localhost:7010/api/event-store/replay/checkout/..." }
```

2) Suivre l’exécution (replay Event Store):
```bash
CHECKOUT_ID=<ID_REPONSE>
curl -s http://localhost:7010/api/event-store/replay/checkout/$CHECKOUT_ID | jq
```

3) Vérifier la projection CQRS (par client):
```bash
curl -s http://localhost:7010/api/event-store/cqrs/orders-by-client/$CLIENT_UUID | jq
```

## Simuler des échecs

1) Stock insuffisant (StockReservationFailed):
```bash
curl -s -X POST \
  http://localhost:8080/ecommerce/api/commandes/clients/$CLIENT_UUID/checkout/choreo/ \
  -H 'Content-Type: application/json' \
  -d '{ "panier": { "lignes": [ { "produit_id": "'$PRODUIT_UUID'", "quantite": 999999 } ] } }'
```
Puis rejouer l’état:
```bash
curl -s http://localhost:7010/api/event-store/replay/checkout/$CHECKOUT_ID | jq
# Attendu: status=failed, reason=StockReservationFailed, éventuel StockReleased
```

2) Échec création commande (OrderCreationFailed):
Stopper temporairement le service commandes pour simuler l’échec:
```bash
docker-compose stop commandes-service
# lancer un checkout normal…
docker-compose start commandes-service
```
Rejouer l’état pour observer `OrderCreationFailed` → `CheckoutFailed` et la compensation (StockReleased).

## Event Store – Endpoints utiles
```bash
# Derniers événements du topic checkout
curl -s 'http://localhost:7010/api/event-store/streams/ecommerce.checkout.events/events?count=100' | jq

# Replay d'un checkout précis
curl -s http://localhost:7010/api/event-store/replay/checkout/$CHECKOUT_ID | jq

# Projection CQRS (read model) par client
curl -s http://localhost:7010/api/event-store/cqrs/orders-by-client/$CLIENT_UUID | jq
```

## Observabilité & métriques

Prometheus (config `config/prometheus.yml`) scrape:
- `lab7-workers` (9100-9105)
- `ecommerce-service` (8005)
- `saga-orchestrator` (8009) – pour comparaison avec le Labo 6

Métriques clés (workers Labo 7):
- `events_published_total{topic,type}`
- `events_consumed_total{topic,type,consumer}`
- `event_latency_seconds{topic,type}`
- `saga_choreo_success_total{source}` / `saga_choreo_failed_total{source}`

Idées de dashboards Grafana:
- Taux succès/échec par type d’événement et par worker
- Débit pub/consommation par topic
- Latence end-to-end (P50/P95) orchestrée vs chorégraphiée

## Débogage & tips

Inspecter les consumer groups Redis Streams:
```bash
docker exec -it redis redis-cli XINFO GROUPS ecommerce.checkout.events
```

Suivre les logs d’un worker:
```bash
docker logs -f stock-reservation-worker
docker logs -f order-creation-worker
docker logs -f stock-compensation-worker
```

Vérifier la consommation/publication:
```bash
docker logs -f audit-worker | grep -i consumed
```

## Variables d’environnement (extraits)

- `REDIS_URL` (par défaut `redis://redis:6379/0`)
- `KONG_URL` (accès interne containers, ex: `http://kong:8000`)
- `API_KEY` (si plugin d’auth sur Kong)
- `METRICS_PORT` (exposition Prometheus sur chaque worker)

## Structure (extrait)
```plaintext
LOG430-Labo7/
├── lab7/
│   ├── common/
│   ├── consumers/
│   └── event_store/
├── service-*/
├── config/
├── docs/
└── docker-compose.yml
```

## Documentation
- Arc42: `docs/arc42.md`
- UML: `docs/UML/`
