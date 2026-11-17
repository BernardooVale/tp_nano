"""
Servidor Web (HTTP + API REST) para o Simulador Visual de Circuitos Polimórficos BP SB-FET.
Executa o ngspice-47 localmente e serve a interface interativa em http://localhost:8000.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from spice_compiler import CompilationError, compile_and_simulate  # noqa: E402
from templates_catalog import CIRCUIT_TEMPLATES, TUPLE_DEFINITIONS  # noqa: E402

STATIC_DIR = os.path.join(CURRENT_DIR, "static")


class SimulatorHandler(BaseHTTPRequestHandler):
    """Manipulador HTTP para arquivos estáticos e endpoints /api/*."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"[BP-FET Studio] {self.address_string()} - {format % args}\n")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, rel_path: str) -> None:
        clean = rel_path.lstrip("/") or "index.html"
        safe_path = os.path.normpath(os.path.join(STATIC_DIR, clean))
        if not safe_path.startswith(os.path.abspath(STATIC_DIR)) or not os.path.isfile(safe_path):
            self.send_error(404, "Arquivo não encontrado")
            return

        ctype, _ = mimetypes.guess_type(safe_path)
        if safe_path.endswith(".js"):
            ctype = "application/javascript; charset=utf-8"
        elif safe_path.endswith(".css"):
            ctype = "text/css; charset=utf-8"
        elif safe_path.endswith(".html"):
            ctype = "text/html; charset=utf-8"
        elif not ctype:
            ctype = "application/octet-stream"

        with open(safe_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {"ok": True, "engine": "ngspice-47"})
            return

        if path == "/api/tuples":
            self._send_json(200, {"tuples": TUPLE_DEFINITIONS})
            return

        if path == "/api/templates":
            self._send_json(200, {"templates": CIRCUIT_TEMPLATES})
            return

        self._send_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/simulate":
            self._send_json(404, {"ok": False, "error": "Rota não encontrada"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": f"JSON inválido: {exc}"})
            return

        try:
            result = compile_and_simulate(payload)
            self._send_json(200, result)
        except CompilationError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            traceback.print_exc()
            self._send_json(500, {"ok": False, "error": f"Erro ao executar ngspice: {exc}"})


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), SimulatorHandler)


if __name__ == "__main__":
    host = os.environ.get("BPFET_HOST", "127.0.0.1")
    port = int(os.environ.get("BPFET_PORT", "8000"))
    server = create_server(host, port)
    print(f"BP-FET Studio rodando em http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        server.server_close()
