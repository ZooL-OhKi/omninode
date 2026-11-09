"""Local headless control server for OmniNode desktop actions."""
import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from desktop_control import DesktopSession, windows_backend

TOKEN = os.environ.get("OMNI_CONTROL_TOKEN")
PORT = int(os.environ.get("OMNI_CONTROL_PORT", "8765"))

if not TOKEN or len(TOKEN) < 32:
    raise SystemExit("OMNI_CONTROL_TOKEN mancante o troppo corto (minimo 32 caratteri)")

session = DesktopSession(
    windows_backend(),
    "local-control",
    ttl=int(os.environ.get("OMNI_CONTROL_TTL", "86400")),
)
lock = threading.Lock()


class ControlHandler(BaseHTTPRequestHandler):
    def _authorized(self):
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {TOKEN}"

    def _json(self, obj, status=200):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._json({"ok": True, "service": "omninode-desktop-control"})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/execute":
            self.send_error(404)
            return
        if not self._authorized():
            self.send_error(401)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            action = data["action"]
            args = data["args"]
            with lock:
                result = session.execute(session.credential(), "local-control", action, args)
            payload = {"ok": True, "result": result}
        except Exception as exc:
            payload = {"ok": False, "error": str(exc)}
        self._json(payload)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), ControlHandler)
    server.serve_forever()
