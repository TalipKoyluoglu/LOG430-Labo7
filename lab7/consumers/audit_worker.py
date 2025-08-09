import json
import os
import time
from prometheus_client import start_http_server
from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import events_consumed_counter, event_latency_seconds


def handle_event(message_id: str, event: dict) -> None:
    etype = event.get("type")
    payload = event.get("payload", {})
    emitted_at = payload.get("emitted_at")
    if emitted_at:
        try:
            latency = max(0.0, time.time() - float(emitted_at))
            event_latency_seconds.labels(topic="ecommerce.checkout.events", type=etype).observe(latency)
        except Exception:
            pass
    events_consumed_counter.labels(topic="ecommerce.checkout.events", type=etype, consumer="audit").inc()
    # Persist JSON line for audit trail
    print(json.dumps({"consumer": "audit", "id": message_id, "type": etype, "payload": payload}, ensure_ascii=False))


def main() -> None:
    start_http_server(int(os.getenv("METRICS_PORT", "9101")))
    bus = RedisEventBus()
    bus.subscribe(
        topic="ecommerce.checkout.events",
        group="checkout-audit",
        consumer=os.getenv("CONSUMER_NAME", "audit-1"),
        handler=handle_event,
        block_ms=5000,
    )


if __name__ == "__main__":
    main()


