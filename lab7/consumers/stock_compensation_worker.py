import os
import time
import requests
from prometheus_client import start_http_server
from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import (
    events_consumed_counter,
    event_latency_seconds,
    saga_choreo_failed_total,
)


KONG_URL = os.getenv("KONG_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "magasin-secret-key-2025")


def liberer_stocks(panier: dict) -> None:
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}
    for p in panier.get("produits", []):
        body = {
            "produit_id": p["produit_id"],
            "quantite": p["quantite"],
        }
        url = f"{KONG_URL}/api/inventaire/api/ddd/inventaire/augmenter-stock/"
        try:
            requests.post(url, json=body, headers=headers, timeout=10)
        except Exception:
            pass


def main() -> None:
    start_http_server(int(os.getenv("METRICS_PORT", "9104")))
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
        events_consumed_counter.labels(topic="ecommerce.checkout.events", type=etype, consumer="stock-compensation").inc()

        if etype not in ("OrderCreationFailed", "StockReservationFailed"):
            return

        liberer_stocks(payload.get("panier", {}))
        bus.publish(
            "ecommerce.checkout.events",
            "StockReleased",
            {
                "checkout_id": payload.get("checkout_id"),
                "emitted_at": time.time(),
            },
        )
        bus.publish(
            "ecommerce.checkout.events",
            "CheckoutFailed",
            {
                "checkout_id": payload.get("checkout_id"),
                "reason": payload.get("reason", "compensation"),
                "emitted_at": time.time(),
            },
        )
        saga_choreo_failed_total.labels(source="stock-compensation").inc()

    bus.subscribe(
        topic="ecommerce.checkout.events",
        group="choreo-compensation",
        consumer=os.getenv("CONSUMER_NAME", "stock-compensator-1"),
        handler=handler,
        block_ms=5000,
    )


if __name__ == "__main__":
    main()


