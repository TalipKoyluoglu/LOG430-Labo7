import json
import os
import time
from typing import Callable, Dict, Optional

import redis


class RedisEventBus:
    """
    Very small Redis Streams-based event bus wrapper.
    - publish(topic, event_type, payload)
    - subscribe(topic, group, consumer, handler)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        stream_max_len: int = 10000,
    ) -> None:
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        self.stream_max_len = stream_max_len

    def publish(self, topic: str, event_type: str, payload: Dict) -> str:
        body = {
            "type": event_type,
            "payload": json.dumps(payload, ensure_ascii=False),
            "ts": str(time.time()),
        }
        message_id = self.client.xadd(topic, body, maxlen=self.stream_max_len, approximate=True)
        return message_id

    def ensure_consumer_group(self, topic: str, group: str) -> None:
        try:
            self.client.xgroup_create(topic, group, id="$", mkstream=True)
        except redis.ResponseError as e:
            # Group exists
            if "BUSYGROUP" in str(e):
                return
            raise

    def subscribe(
        self,
        topic: str,
        group: str,
        consumer: str,
        handler: Callable[[str, Dict], None],
        block_ms: int = 5000,
    ) -> None:
        """
        Blocking loop. For each message: calls handler(message_id, {"type": str, "payload": dict, "ts": str}).
        Handler must be idempotent.
        """
        self.ensure_consumer_group(topic, group)
        while True:
            resp = self.client.xreadgroup(group, consumer, {topic: ">"}, count=10, block=block_ms)
            if not resp:
                continue
            for _, messages in resp:
                for message_id, fields in messages:
                    try:
                        payload = json.loads(fields.get("payload", "{}"))
                    except json.JSONDecodeError:
                        payload = {"_raw": fields.get("payload")}
                    event = {"type": fields.get("type"), "payload": payload, "ts": fields.get("ts")}
                    try:
                        handler(message_id, event)
                        self.client.xack(topic, group, message_id)
                    except Exception:
                        # Do not ACK so it can be retried by another consumer/after restart
                        pass


