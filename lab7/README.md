# Labo 7 – Event-driven, Event Sourcing, CQRS, Saga chorégraphiée

## Démarrage

1) Lancer l'infrastructure (incluant Redis et l'Event Store API):
```bash
docker-compose up -d
```

2) Lancer des consommateurs en local (optionnel):
```bash
python lab7/consumers/notification_worker.py
python lab7/consumers/audit_worker.py
python lab7/consumers/stock_reservation_worker.py
python lab7/consumers/order_creation_worker.py
python lab7/consumers/stock_compensation_worker.py
```

## Événements

Topic principal: `ecommerce.checkout.events`
- `CheckoutInitiated` { checkout_id, client_id, panier, emitted_at }
- `StockReserved` { checkout_id, client_id, panier, emitted_at }
- `StockReservationFailed` { checkout_id, reason, emitted_at }
- `OrderCreated` { checkout_id, commande_id, emitted_at }
- `OrderCreationFailed` { checkout_id, reason, emitted_at }
- `StockReleased` { checkout_id, emitted_at }
- `CheckoutSucceeded` { checkout_id, commande_id, emitted_at }
- `CheckoutFailed` { checkout_id, reason, emitted_at }

## APIs

- Checkout synchrone (orchestration existante):
  POST `service-ecommerce` `/api/commandes/clients/{client_id}/checkout/`
- Checkout chorégraphié (asynchrone):
  POST `service-ecommerce` `/api/commandes/clients/{client_id}/checkout/choreo/`
  -> 202 Accepted + `checkout_id` et lien de suivi replay
- Event Store (lecture):
  - GET `http://localhost:7010/api/event-store/streams/ecommerce.checkout.events/events`
  - GET `http://localhost:7010/api/event-store/replay/checkout/{checkout_id}`

## Observabilité

Prometheus et Grafana sont déjà configurés. Les métriques événementielles exposées:
- `events_published_total{topic,type}`
- `events_consumed_total{topic,type,consumer}`
- `event_latency_seconds_bucket|sum|count{topic,type}`


