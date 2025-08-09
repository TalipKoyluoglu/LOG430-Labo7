import os
import time
import requests
from prometheus_client import start_http_server
from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import events_consumed_counter, event_latency_seconds


KONG_URL = os.getenv("KONG_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "magasin-secret-key-2025")


def reserver_stocks(panier_resume: dict) -> bool:
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
    for p in panier_resume.get("produits", []):
        body = {
            "produit_id": p["produit_id"],
            "quantite": p["quantite"],
        }
        # Stock central (pas de magasin_id)
        url = f"{KONG_URL}/api/inventaire/api/ddd/inventaire/diminuer-stock/"
        resp = requests.post(url, json=body, headers=headers, timeout=10)
        if resp.status_code != 200:
            return False
    return True


def main() -> None:
    start_http_server(int(os.getenv("METRICS_PORT", "9102")))
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
        events_consumed_counter.labels(topic="ecommerce.checkout.events", type=etype, consumer="stock-reservation").inc()

        if etype != "CheckoutInitiated":
            return

        # Try to reserve stock; publish success/failure
        success = reserver_stocks(payload.get("panier", {}))
        if success:
            bus.publish(
                "ecommerce.checkout.events",
                "StockReserved",
                {
                    "checkout_id": payload.get("checkout_id"),
                    "client_id": payload.get("client_id"),
                    "panier": payload.get("panier", {}),
                    "emitted_at": time.time(),
                },
            )
        else:
            bus.publish(
                "ecommerce.checkout.events",
                "StockReservationFailed",
                {
                    "checkout_id": payload.get("checkout_id"),
                    "reason": "inventory_error",
                    "emitted_at": time.time(),
                },
            )

    bus.subscribe(
        topic="ecommerce.checkout.events",
        group="choreo-reservation",
        consumer=os.getenv("CONSUMER_NAME", "stock-reserver-1"),
        handler=handler,
        block_ms=5000,
    )


if __name__ == "__main__":
    main()


