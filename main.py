"""
AgriTwin-ZM v1.0 - Main Entry Point

Launches either the Tkinter GUI application or a lightweight JSON API.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from gui import main as launch_gui
from models.maize import Maize
from models.tomato import Tomato
from engines.supply_demand import SupplyDemandEngine


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _run_maize_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    production = float(payload.get("production", 0))
    demand = float(payload.get("demand", 0))
    moisture = float(payload.get("moisture", 13.5))
    price = float(payload.get("price_per_ton", 4500))
    loss_pct = float(payload.get("loss_percentage_per_month", 3.0))
    storage_capacity = float(payload.get("storage_capacity", 60000))
    month_name = str(payload.get("month", "Month-1"))

    maize = Maize(production, storage_capacity, moisture, price, loss_pct)
    engine = SupplyDemandEngine(maize, production, demand)
    return engine.run_monthly_simulation(month_name, maize.calculate_monthly_loss())


def _run_tomato_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    production = float(payload.get("production", 0))
    demand = float(payload.get("demand", 0))
    shelf_life = int(payload.get("shelf_life_days", 14))
    storage_type = str(payload.get("storage_type", "open"))
    spoilage_rate = float(payload.get("spoilage_rate", 1.5 if storage_type == "cold" else 4.0))
    price_crate = float(payload.get("market_price_per_crate", 120))
    month_name = str(payload.get("month", "Month-1"))

    tomato = Tomato(production, shelf_life, storage_type, spoilage_rate, price_crate)
    spoilage_tons = tomato.calculate_spoilage(shelf_life)["total_spoilage_tons"]
    engine = SupplyDemandEngine(tomato, production, demand)
    return engine.run_monthly_simulation(month_name, spoilage_tons)


class AgriTwinApiHandler(BaseHTTPRequestHandler):
    """Minimal API handler for web/mobile integration."""

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/api/health":
            _json_response(self, 200, {"status": "ok", "service": "AgriTwin-ZM API"})
            return
        _json_response(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8") or "{}")

            endpoint = self.path.rstrip("/")
            if endpoint == "/api/simulate/maize":
                result = _run_maize_from_payload(payload)
            elif endpoint == "/api/simulate/tomato":
                result = _run_tomato_from_payload(payload)
            else:
                _json_response(self, 404, {"error": "Not found"})
                return

            _json_response(self, 200, {"ok": True, "result": result})
        except Exception as exc:
            _json_response(self, 400, {"ok": False, "error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        # Keep console output clean for local development.
        return


def launch_api(host: str, port: int) -> None:
    server = HTTPServer((host, port), AgriTwinApiHandler)
    print(f"AgriTwin API running at http://{host}:{port}")
    print("Endpoints: GET /api/health, POST /api/simulate/maize, POST /api/simulate/tomato")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AgriTwin-ZM launcher")
    parser.add_argument("--mode", choices=["gui", "api"], default="gui", help="Launch mode")
    parser.add_argument("--host", default="127.0.0.1", help="API host when mode=api")
    parser.add_argument("--port", default=8000, type=int, help="API port when mode=api")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "api":
        launch_api(args.host, args.port)
    else:
        launch_gui()


if __name__ == "__main__":
    main()
