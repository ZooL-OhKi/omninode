"""Opt-in desktop primitives; no listener, autostart, or chat transport."""
import hmac
import io
import secrets
import threading
import time


class DesktopSession:
    """Construct only after local consent; credentials stay in trusted contexts."""

    def __init__(self, backend, conversation, ttl=600, clock=time.monotonic):
        if not isinstance(conversation, str) or not conversation or not 1 <= ttl <= 900:
            raise ValueError("invalid local grant")
        self._backend = backend
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
                or conversation != self._conversation
                or not isinstance(token, str)
                or not hmac.compare_digest(token.encode(), self._token.encode())):
            raise PermissionError("desktop grant absent, expired, stopped, or mismatched")

    def execute(self, token, conversation, action, args):
        schemas = {"screenshot": set(), "move": {"x", "y"},
                   "click": {"x", "y", "button"}, "scroll": {"steps"},
                   "press": {"key"}, "hotkey": {"keys"}, "type": {"text"},
                   "drag": {"x", "y", "to_x", "to_y"}}
        with self._lock:
            self._check(token, conversation)
            if not isinstance(action, str) or action not in schemas or not isinstance(args, dict) or set(args) != schemas[action]:
                raise ValueError("unsupported action or invalid schema")
            b = self._backend
            width, height = b.size()
            def point(x, y):
                if type(x) is not int or type(y) is not int or not (0 <= x < width and 0 <= y < height):
                    raise ValueError("coordinates outside primary display")
            def key(k):
                if not isinstance(k, str) or k not in b.KEYBOARD_KEYS:
                    raise ValueError("unsupported key")
            try:
                if action == "screenshot":
                    image = b.screenshot()
                    stream = io.BytesIO()
                    image.save(stream, format="PNG")
                    self._check(token, conversation)
                    return {"mime": "image/png", "width": image.width,
                            "height": image.height, "data": stream.getvalue()}
                if action in {"move", "click", "drag"}:
                    point(args["x"], args["y"])
                if action == "click" and args["button"] not in {"left", "right", "middle"}:
                    raise ValueError("unsupported mouse button")
                if action == "drag":
                    point(args["to_x"], args["to_y"])
                if action == "scroll":
                    if type(args["steps"]) is not int or not -20 <= args["steps"] <= 20:
                        raise ValueError("scroll limit exceeded")
                if action == "press":
                    key(args["key"])
                if action == "hotkey":
                    if not isinstance(args["keys"], list) or not 1 <= len(args["keys"]) <= 4:
                        raise ValueError("hotkey limit exceeded")
                    for k in args["keys"]:
                        key(k)
                if action == "type":
                    text = args["text"]
                    if not isinstance(text, str) or not 1 <= len(text) <= 4096 or any(ord(c) < 32 or ord(c) > 126 for c in text):
                        raise ValueError("first backend accepts printable ASCII only; use press for control keys")
                self._check(token, conversation)
                if action == "move":
                    b.moveTo(args["x"], args["y"])
                elif action == "click":
                    b.click(args["x"], args["y"], button=args["button"])
                elif action == "scroll":
                    b.scroll(args["steps"])
                elif action == "press":
                    b.press(args["key"])
                elif action == "type":
                    for char in args["text"]:
                        self._check(token, conversation)
                        b.write(char)
                elif action == "hotkey":
                    held = []
                    try:
                        for k in args["keys"]:
                            self._check(token, conversation)
                            b.keyDown(k)
                            held.append(k)
                    finally:
                        for k in reversed(held):
                            b.keyUp(k, _pause=False)
                elif action == "drag":
                    b.moveTo(args["x"], args["y"])
                    self._check(token, conversation)
                    b.mouseDown()
                    try:
                        for step in range(1, 21):
                            self._check(token, conversation)
                            x = round(args["x"] + (args["to_x"] - args["x"]) * step / 20)
                            y = round(args["y"] + (args["to_y"] - args["y"]) * step / 20)
                            b.moveTo(x, y)
                    finally:
                        b.mouseUp(_pause=False)
                self._check(token, conversation)
                return {"status": "executed", "action": action}
            except b.FailSafeException:
                self.stop()
                raise PermissionError("desktop emergency stop") from None


def windows_backend():
    import sys
    if sys.platform != "win32":
        raise RuntimeError("native backend currently supports Windows only")
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    return pyautogui
