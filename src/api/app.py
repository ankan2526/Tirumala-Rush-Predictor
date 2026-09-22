"""HTTP REST API and Static Web Server for Tirumala Tirupati Rush Predictor.

Uses standard library http.server for 100% dependency-free operation across any environment.
"""

from __future__ import annotations
import argparse
import json
import mimetypes
import os
import sys
from datetime import date, datetime, timedelta
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.models.predictor import TirumalaRushPredictor


class TirumalaAPIHandler(SimpleHTTPRequestHandler):
    """Handles REST API requests and serves static web dashboard assets."""

    predictor: TirumalaRushPredictor = TirumalaRushPredictor()
    web_dir: Path = Path(__file__).resolve().parent.parent / "web"

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests to API endpoints or static web assets."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API routing
        if path.startswith("/api/"):
            self.handle_api(path, query)
            return

        # Static assets routing
        self.handle_static(path)

    def handle_api(self, path: str, query: dict) -> None:
        """Handle REST API endpoints."""
        try:
            if path == "/api/predict":
                date_str = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                result = self.predictor.predict_date(target_date)
                self.send_json_response(result)

            elif path == "/api/calendar":
                now = datetime.now()
                year = int(query.get("year", [now.year])[0])
                month = int(query.get("month", [now.month])[0])
                result = self.predictor.predict_month(year, month)
                self.send_json_response({"year": year, "month": month, "days": result})

            elif path == "/api/recommend":
                today = date.today()
                start_str = query.get("start", [today.strftime("%Y-%m-%d")])[0]
                end_str = query.get("end", [(today + timedelta(days=30)).strftime("%Y-%m-%d")])[0]
                darshan_type = query.get("ticket", ["all"])[0]

                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

                if (end_date - start_date).days > 120:
                    self.send_error_json("Date range cannot exceed 120 days", HTTPStatus.BAD_REQUEST)
                    return

                recommendations = self.predictor.recommend_best_dates(
                    start_date=start_date,
                    end_date=end_date,
                    darshan_type=darshan_type,
                    max_results=8
                )
                self.send_json_response({
                    "start_date": start_str,
                    "end_date": end_str,
                    "darshan_type": darshan_type,
                    "recommendations": recommendations
                })

            elif path == "/api/live-status":
                today = date.today()
                pred = self.predictor.predict_date(today)
                yesterday = today - timedelta(days=1)
                y_pred = self.predictor.predict_date(yesterday)

                self.send_json_response({
                    "server_time": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                    "today": pred,
                    "yesterday_bulletin": {
                        "report_date": yesterday.strftime("%d-%m-%Y"),
                        "darshan_count": y_pred["estimated_pilgrims"],
                        "hundi_crores": y_pred["est_hundi_crores"],
                        "tonsures": y_pred["est_tonsures"],
                        "laddus_distributed": y_pred["est_laddus"],
                        "compartments_filled": y_pred["compartments_filled"],
                        "sarva_darshan_wait_hours": y_pred["sarva_darshan_wait_hours"]
                    }
                })

            elif path == "/api/insights":
                # Load model weights if available
                weights_path = Path(__file__).resolve().parent.parent.parent / "data" / "model_weights.json"
                weights_data = {}
                if weights_path.exists():
                    with open(weights_path, "r", encoding="utf-8") as f:
                        weights_data = json.load(f)

                # Day of week statistics
                dow_distribution = [
                    {"day": "Monday", "avg_pilgrims": 63500, "rush_tier": "Moderate", "wait_hours": 9.5},
                    {"day": "Tuesday", "avg_pilgrims": 53000, "rush_tier": "Low (Best Day)", "wait_hours": 5.5},
                    {"day": "Wednesday", "avg_pilgrims": 52000, "rush_tier": "Low (Best Day)", "wait_hours": 5.0},
                    {"day": "Thursday", "avg_pilgrims": 55000, "rush_tier": "Low", "wait_hours": 6.5},
                    {"day": "Friday", "avg_pilgrims": 71000, "rush_tier": "Moderate-High", "wait_hours": 13.0},
                    {"day": "Saturday", "avg_pilgrims": 86000, "rush_tier": "Peak", "wait_hours": 24.0},
                    {"day": "Sunday", "avg_pilgrims": 81000, "rush_tier": "Peak", "wait_hours": 20.5},
                ]

                # Monthly seasonality index
                monthly_seasonality = [
                    {"month": "Jan", "name": "January", "index": 1.15, "surge_event": "Vaikunta Dwara & Sankranti"},
                    {"month": "Feb", "name": "February", "index": 0.85, "surge_event": "Exam Season Starts (Lean)"},
                    {"month": "Mar", "name": "March", "index": 0.78, "surge_event": "School Exams (Leanest Month)"},
                    {"month": "Apr", "name": "April", "index": 1.10, "surge_event": "Ugadi & Summer Rush Begins"},
                    {"month": "May", "name": "May", "index": 1.35, "surge_event": "Summer Vacation Peak"},
                    {"month": "Jun", "name": "June", "index": 1.25, "surge_event": "Summer Rush Wind-down"},
                    {"month": "Jul", "name": "July", "index": 0.95, "surge_event": "Monsoon Academic Term"},
                    {"month": "Aug", "name": "August", "index": 1.05, "surge_event": "Shravana Masam Auspicious Days"},
                    {"month": "Sep", "name": "September", "index": 1.30, "surge_event": "Purattasi Masam & Brahmotsavam"},
                    {"month": "Oct", "name": "October", "index": 1.35, "surge_event": "Navaratri & Dussehra Holidays"},
                    {"month": "Nov", "name": "November", "index": 1.12, "surge_event": "Karthika Masam Deepotsavam"},
                    {"month": "Dec", "name": "December", "index": 1.28, "surge_event": "Year End & Vaikunta Dwara"},
                ]

                self.send_json_response({
                    "model_weights": weights_data,
                    "dow_distribution": dow_distribution,
                    "monthly_seasonality": monthly_seasonality
                })

            else:
                self.send_error_json("Endpoint not found", HTTPStatus.NOT_FOUND)

        except ValueError as ve:
            self.send_error_json(f"Invalid parameter format: {ve}", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            self.send_error_json(f"Internal server error: {e}", HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_static(self, path: str) -> None:
        """Serve HTML/CSS/JS frontend files."""
        if path in ("/", ""):
            file_path = self.web_dir / "index.html"
        elif path.startswith("/static/"):
            subpath = path[len("/static/"):]
            file_path = self.web_dir / "static" / subpath
        else:
            file_path = self.web_dir / path.lstrip("/")

        # Check safety and existence
        try:
            resolved = file_path.resolve()
            if not str(resolved).startswith(str(self.web_dir.resolve())):
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
        except Exception:
            self.send_error(HTTPStatus.NOT_FOUND, "File Not Found")
            return

        if not resolved.exists() or resolved.is_dir():
            if (self.web_dir / "index.html").exists():
                file_path = self.web_dir / "index.html"
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "File Not Found")
                return

        ctype, _ = mimetypes.guess_type(str(file_path))
        if ctype is None:
            ctype = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def send_json_response(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        """Serialize and send JSON response."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        """Send error message as structured JSON."""
        self.send_json_response({"error": True, "message": message, "status": status.value}, status)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy request logs, keeping terminal output clean."""
        pass


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start HTTP server."""
    server = HTTPServer((host, port), TirumalaAPIHandler)
    print(f"🛕 Tirumala Tirupati Rush Predictor Web Dashboard running at http://localhost:{port}")
    print(f"📡 API Endpoints available:")
    print(f"   - GET http://localhost:{port}/api/predict?date=YYYY-MM-DD")
    print(f"   - GET http://localhost:{port}/api/calendar?year=YYYY&month=MM")
    print(f"   - GET http://localhost:{port}/api/recommend?start=YYYY-MM-DD&end=YYYY-MM-DD")
    print(f"   - GET http://localhost:{port}/api/live-status")
    print(f"   - GET http://localhost:{port}/api/insights")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        server.server_close()


def create_app_handler():
    return TirumalaAPIHandler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tirumala Tirupati Rush Predictor Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    args = parser.parse_args()
    run_server(args.host, args.port)
