"""Desktop grants, validation and operation deadlines; no network listener."""
import hmac
import secrets
import threading
import time
from windows_input_backend import WindowsInputBackend, make_windows_backend

OP_BUDGET_SEC = 12.0
SCHEMAS = {"screenshot": set(), "move": {"x", "y"}, "click": {"x", "y", "button"},
           "scroll": {"steps"}, "press": {"key"}, "hotkey": {"keys"},
           "type": {"text"}, "drag": {"x", "y", "to_x", "to_y"},
           "notepad_write": {"x", "y", "text"}}


class DesktopSession:
    def __init__(self, backend, conversation, ttl=600, clock=time.monotonic):
        if not isinstance(conversation, str) or not conversation or not 1 <= ttl <= 900:
            raise ValueError("invalid local grant")
        self._backend = backend
        self._executor = backend if isinstance(backend, WindowsInputBackend) else WindowsInputBackend(backend)
        self._conversation = conversation
        self._clock = clock
        self._expires = clock() + ttl
        self._token = secrets.token_urlsafe(32)
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def credential(self):
        return self._token

    def stop(self):
        self._stop.set()

    def _check(self, token, conversation):
        if (self._stop.is_set() or self._clock() >= self._expires
                or conversation != self._conversation or not isinstance(token, str)
                or not hmac.compare_digest(token.encode(), self._token.encode())):
            raise PermissionError("desktop grant absent, expired, stopped, or mismatched")

    def _validate(self, action, args):
        if not isinstance(action, str) or action not in SCHEMAS or not isinstance(args, dict) or set(args) != SCHEMAS[action]:
            raise ValueError("unsupported action or invalid schema")
        width, height = self._executor.size()

        def point(x, y):
            if type(x) is not int or type(y) is not int or not (0 <= x < width and 0 <= y < height):
                raise ValueError("coordinates outside primary display")

        def key(value):
            if not self._executor.valid_key(value):
                raise ValueError("unsupported key")

        if action in {"move", "click", "drag", "notepad_write"}:
            point(args["x"], args["y"])
        if action == "drag":
            point(args["to_x"], args["to_y"])
        if action == "click" and args["button"] not in {"left", "right", "middle"}:
            raise ValueError("unsupported mouse button")
        if action == "scroll" and (type(args["steps"]) is not int or not -20 <= args["steps"] <= 20):
            raise ValueError("scroll limit exceeded")
        if action == "press":
            key(args["key"])
        if action == "hotkey":
            if not isinstance(args["keys"], list) or not 1 <= len(args["keys"]) <= 4:
                raise ValueError("hotkey limit exceeded")
            for value in args["keys"]:
                key(value)
        if action in {"type", "notepad_write"}:
            text = args["text"]
            limit = 256 if self._executor.natural or action == "notepad_write" else 4096
            if not isinstance(text, str) or not 1 <= len(text) <= limit:
                raise ValueError("text limit exceeded")
            if any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xd800 <= ord(c) <= 0xdfff for c in text):
                raise ValueError("use press for control keys")
            if not self._executor.natural and any(ord(c) > 126 for c in text):
                raise ValueError("backend accepts printable ASCII only")

    def execute(self, token, conversation, action, args):
        with self._lock:
            self._check(token, conversation)
            deadline = self._clock() + OP_BUDGET_SEC

            def check():
                self._check(token, conversation)
                if self._clock() >= deadline:
                    self.stop()
                    raise TimeoutError("operation deadline exceeded; do not retry")

            def wait(seconds):
                check()
                self._stop.wait(min(seconds, max(0.0, deadline - self._clock())))
                check()

            self._validate(action, args)
            check()
            try:
                if action == "notepad_write":
                    from notepad_task import run_notepad_write
                    result = run_notepad_write(self._executor, args, check, wait)
                else:
                    result = self._executor.perform(action, args, check, wait)
                check()
                return result
            except self._executor.raw.FailSafeException:
                self.stop()
                raise PermissionError("desktop emergency stop") from None
            except Exception:
                self.stop()
                raise


def windows_backend():
    return make_windows_backend()
