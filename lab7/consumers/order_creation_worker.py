import os
import time
import requests
from prometheus_client import start_http_server
from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import (
    events_consumed_counter,
    event_latency_seconds,
    saga_choreo_success_total,
)


KONG_URL = os.getenv("KONG_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "magasin-secret-key-2025")


def creer_commande(checkout_id: str, client_id: str, panier: dict) -> str | None:
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
    # Map sur le service-commandes DDD (vente unique simplifiée): prendre le premier produit
    if not panier.get("produits"):
        return None
    ligne = panier["produits"][0]
    # Utiliser un magasin valide connu du service-commandes (voir service-commandes/initial_data.json)
    default_magasin_id = os.getenv(
        "DEFAULT_MAGASIN_ID",
        "33333333-3333-3333-3333-333333333331",
    )
    body = {
        "magasin_id": default_magasin_id,
        "client_id": client_id,
        "produit_id": ligne["produit_id"],
        "quantite": int(ligne["quantite"]),
    }
    url = f"{KONG_URL}/api/commandes/api/v1/ventes-ddd/enregistrer/"
    resp = requests.post(url, json=body, headers=headers, timeout=15)
    if resp.status_code == 201:
        data = resp.json()
        return data.get("vente", {}).get("id") or data.get("vente_id")
    return None


def main() -> None:
    start_http_server(int(os.getenv("METRICS_PORT", "9103")))
    bus = RedisEventBus()

    def handler(message_id: str, event: dict) -> None:
        etype = event.get("type")
        payload = event.get("payload", {})
        emitted_at = payload.get("emitted_at")
        if emitted_at:
            try:
                latency = max(0.0, time.time() - float(emitted_at))
                event_latency_seconds.labels(topic="ecommerce.checkout.events", type=etype).observe(latency)
            except Exception:
                pass
        events_consumed_counter.labels(topic="ecommerce.checkout.events", type=etype, consumer="order-creator").inc()

        if etype != "StockReserved":
            return

        checkout_id = payload.get("checkout_id")
        client_id = payload.get("client_id")
        panier = payload.get("panier", {})

        commande_id = creer_commande(checkout_id, client_id, panier)
        if commande_id:
            bus.publish(
                "ecommerce.checkout.events",
                "OrderCreated",
                {
                    "checkout_id": checkout_id,
                    "commande_id": commande_id,
                    "client_id": client_id,
                    "emitted_at": time.time(),
                },
            )
            bus.publish(
                "ecommerce.checkout.events",
                "CheckoutSucceeded",
                {
                    "checkout_id": checkout_id,
                    "commande_id": commande_id,
                    "emitted_at": time.time(),
                },
            )
            saga_choreo_success_total.labels(source="order-creator").inc()
        else:
            bus.publish(
                "ecommerce.checkout.events",
                "OrderCreationFailed",
                {
                    "checkout_id": checkout_id,
                    "reason": "order_service_error",
                    "emitted_at": time.time(),
                },
            )

    bus.subscribe(
        topic="ecommerce.checkout.events",
        group="choreo-order",
        consumer=os.getenv("CONSUMER_NAME", "order-creator-1"),
        handler=handler,
        block_ms=5000,
    )


if __name__ == "__main__":
    main()


