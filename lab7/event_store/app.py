import json
import os
from typing import Any, Dict, List

from flask import Flask, jsonify
from flask import request as flask_request
from redis import Redis


def create_app() -> Flask:
    app = Flask(__name__)
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    client = Redis.from_url(redis_url, decode_responses=True)

    # Simple API to read events from a stream and return a projection example
    @app.get("/api/event-store/streams/<stream>/events")
    def list_events(stream: str):
        count = int(flask_request.args.get("count", 100))
        # Read from the start
        events = client.xrange(stream, min="-", max="+", count=count)
        formatted: List[Dict[str, Any]] = []
        for message_id, fields in events:
            payload = fields.get("payload")
            try:
                payload = json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                payload = {"_raw": payload}
            formatted.append({"id": message_id, "type": fields.get("type"), "ts": fields.get("ts"), "payload": payload})
        return jsonify({"stream": stream, "events": formatted})

    @app.get("/api/event-store/replay/checkout/<checkout_id>")
    def replay_checkout(checkout_id: str):
        # Reconstruct a coarse-grained state based on ecommerce.checkout.events
        events = client.xrange("ecommerce.checkout.events", min="-", max="+")
        state: Dict[str, Any] = {"checkout_id": checkout_id, "status": "unknown", "events": []}
        for message_id, fields in events:
            try:
                payload = json.loads(fields.get("payload", "{}"))
            except json.JSONDecodeError:
                payload = {}
            if payload.get("checkout_id") != checkout_id:
                continue
            etype = fields.get("type")
            # Enrich StockReserved with client/panier if not present
            if etype == "StockReserved":
                state["stock_reserved"] = True
            if etype == "StockReservationFailed":
                state["stock_reserved"] = False
            state["events"].append({"id": message_id, "type": etype, "payload": payload, "ts": fields.get("ts")})
            if etype == "CheckoutInitiated":
                state["status"] = "initiated"
            elif etype == "CheckoutSucceeded":
                state["status"] = "succeeded"
                state["commande_id"] = payload.get("commande_id")
            elif etype == "CheckoutFailed":
                state["status"] = "failed"
                state["reason"] = payload.get("reason")
            elif etype == "OrderCreated":
                state["order"] = {"commande_id": payload.get("commande_id")}
            elif etype == "OrderCreationFailed":
                state["order"] = {"failed": True, "reason": payload.get("reason")}
            elif etype == "StockReleased":
                state["stock_released"] = True
        return jsonify(state)

    @app.get("/api/event-store/cqrs/orders-by-client/<client_id>")
    def get_orders_by_client(client_id: str):
        # Query the Redis CQRS read model
        raw = client.get(f"cqrs:orders_by_client:{client_id}")
        if not raw:
            return jsonify({
                "client_id": client_id,
                "total_orders": 0,
                "message": "no data"
            })
        try:
            data = json.loads(raw)
        except Exception:
            data = {"_raw": raw}
        data["client_id"] = client_id
        return jsonify(data)

    return app


app = create_app()


