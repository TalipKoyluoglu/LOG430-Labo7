import os
import time
import json
from typing import Dict
from redis import Redis
from prometheus_client import start_http_server
from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import events_consumed_counter, event_latency_seconds


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


def update_projection(client: Redis, event_type: str, payload: Dict) -> None:
    """
    Maintains a read model in Redis: key 'cqrs:orders_by_client:{client_id}' → JSON doc
    { total_orders, last_order_id, last_checkout_id, last_update_ts }
    Triggered by OrderCreated / CheckoutSucceeded / CheckoutFailed.
    """
    client_id = payload.get("client_id")
    if not client_id:
        return
    key = f"cqrs:orders_by_client:{client_id}"
    doc: Dict = {}
    raw = client.get(key)
    if raw:
        try:
            doc = json.loads(raw)
        except Exception:
            doc = {}
    doc.setdefault("total_orders", 0)
    if event_type in ("OrderCreated", "CheckoutSucceeded"):
        doc["total_orders"] = int(doc.get("total_orders", 0)) + 1
        if payload.get("commande_id"):
            doc["last_order_id"] = payload.get("commande_id")
    if payload.get("checkout_id"):
        doc["last_checkout_id"] = payload.get("checkout_id")
    doc["last_update_ts"] = time.time()
    client.set(key, json.dumps(doc, ensure_ascii=False))


def main() -> None:
    start_http_server(int(os.getenv("METRICS_PORT", "9105")))
    bus = RedisEventBus()
    r = Redis.from_url(REDIS_URL, decode_responses=True)

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
        events_consumed_counter.labels(topic="ecommerce.checkout.events", type=etype, consumer="cqrs-projection").inc()

        if etype not in ("OrderCreated", "CheckoutSucceeded", "CheckoutFailed"):
            return
        update_projection(r, etype, payload)

    bus.subscribe(
        topic="ecommerce.checkout.events",
        group="checkout-cqrs",
        consumer=os.getenv("CONSUMER_NAME", "cqrs-projection-1"),
        handler=handler,
        block_ms=5000,
    )


if __name__ == "__main__":
    main()


