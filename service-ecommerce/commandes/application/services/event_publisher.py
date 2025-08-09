import time
from typing import Dict

from lab7.common.event_bus import RedisEventBus
from lab7.common.metrics import events_published_counter


class EcommerceEventPublisher:
    def __init__(self) -> None:
        self.bus = RedisEventBus()

    def publish_checkout_initiated(self, checkout_id: str, client_id: str, panier_resume: Dict) -> str:
        payload = {
            "checkout_id": checkout_id,
            "client_id": client_id,
            "panier": panier_resume,
            "emitted_at": time.time(),
        }
        msg_id = self.bus.publish("ecommerce.checkout.events", "CheckoutInitiated", payload)
        events_published_counter.labels(topic="ecommerce.checkout.events", type="CheckoutInitiated").inc()
        return msg_id

    def publish_checkout_succeeded(self, checkout_id: str, commande_id: str) -> str:
        payload = {
            "checkout_id": checkout_id,
            "commande_id": commande_id,
            "emitted_at": time.time(),
        }
        msg_id = self.bus.publish("ecommerce.checkout.events", "CheckoutSucceeded", payload)
        events_published_counter.labels(topic="ecommerce.checkout.events", type="CheckoutSucceeded").inc()
        return msg_id

    def publish_checkout_failed(self, checkout_id: str, reason: str) -> str:
        payload = {"checkout_id": checkout_id, "reason": reason, "emitted_at": time.time()}
        msg_id = self.bus.publish("ecommerce.checkout.events", "CheckoutFailed", payload)
        events_published_counter.labels(topic="ecommerce.checkout.events", type="CheckoutFailed").inc()
        return msg_id


