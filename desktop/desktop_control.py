"""Opt-in desktop primitives with interruptible natural input; no network listener."""
import hmac
import io
import secrets
import threading
import time


class DesktopSession:
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
        self._natural = getattr(backend, "omni_natural", False) is True

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

    def _pause(self, seconds, token, conversation):
        self._stop.wait(seconds)
        self._check(token, conversation)

    def _move(self, x, y, token, conversation):
        b = self._backend
        if not self._natural:
            b.moveTo(x, y)
            return
        start_x, start_y = b.position()
        for step in range(1, 21):
            self._check(token, conversation)
            t = step / 20
            smooth = t * t * (3 - 2 * t)
            b.moveTo(round(start_x + (x - start_x) * smooth),
                     round(start_y + (y - start_y) * smooth), _pause=False)
            self._pause(0.012, token, conversation)

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
                    if self._natural and (image.width, image.height) != (width, height):
                        raise ValueError("screenshot and primary input geometry differ")
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
                if action == "scroll" and (type(args["steps"]) is not int or not -20 <= args["steps"] <= 20):
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
                    limit = 256 if self._natural else 4096
                    if not isinstance(text, str) or not 1 <= len(text) <= limit:
                        raise ValueError("text limit exceeded")
                    if self._natural:
                        if any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xd800 <= ord(c) <= 0xdfff for c in text):
                            raise ValueError("use press for control keys")
                    elif any(ord(c) < 32 or ord(c) > 126 for c in text):
                        raise ValueError("backend accepts printable ASCII only")
                self._check(token, conversation)
                if action == "move":
                    self._move(args["x"], args["y"], token, conversation)
                elif action == "click":
                    if self._natural:
                        self._move(args["x"], args["y"], token, conversation)
                        self._check(token, conversation)
                        b.mouseDown(button=args["button"], _pause=False)
                        try:
                            self._pause(0.045, token, conversation)
                        finally:
                            b.mouseUp(button=args["button"], _pause=False)
                    else:
                        b.click(args["x"], args["y"], button=args["button"])
                elif action == "scroll":
                    if self._natural:
                        for _ in range(abs(args["steps"])):
                            self._check(token, conversation)
                            b.scroll(1 if args["steps"] > 0 else -1, _pause=False)
                            self._pause(0.035, token, conversation)
                    else:
                        b.scroll(args["steps"])
                elif action == "press":
                    if self._natural:
                        b.keyDown(args["key"], _pause=False)
                        try:
                            self._pause(0.045, token, conversation)
                        finally:
                            b.keyUp(args["key"], _pause=False)
                    else:
                        b.press(args["key"])
                elif action == "type":
                    for char in args["text"]:
                        self._check(token, conversation)
                        if self._natural:
                            b.omni_write(char)
                            self._pause(0.045 if char in " ,.;:!?" else 0.018, token, conversation)
                        else:
                            b.write(char)
                elif action == "hotkey":
                    held = []
                    try:
                        for k in args["keys"]:
                            self._check(token, conversation)
                            b.keyDown(k)
                            held.append(k)
                            if self._natural:
                                self._pause(0.025, token, conversation)
                    finally:
                        for k in reversed(held):
                            b.keyUp(k, _pause=False)
                elif action == "drag":
                    self._move(args["x"], args["y"], token, conversation)
                    self._check(token, conversation)
                    b.mouseDown()
                    try:
                        if self._natural:
                            self._move(args["to_x"], args["to_y"], token, conversation)
                        else:
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
    import ctypes
    from ctypes import wintypes
    import pyautogui

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

    class KeyboardInput(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD)]

    class InputUnion(ctypes.Union):
        _fields_ = [("mi", MouseInput), ("ki", KeyboardInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _anonymous_ = ("data",)
        _fields_ = [("type", wintypes.DWORD), ("data", InputUnion)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    send = user32.SendInput
    send.argtypes = (wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int)
    send.restype = wintypes.UINT

    def write_character(char):
        pyautogui.failSafeCheck()
        encoded = char.encode("utf-16-le", errors="strict")
        for offset in range(0, len(encoded), 2):
            unit = int.from_bytes(encoded[offset:offset + 2], "little")
            down = Input(type=1, ki=KeyboardInput(wVk=0, wScan=unit, dwFlags=4))
            up = Input(type=1, ki=KeyboardInput(wVk=0, wScan=unit, dwFlags=6))
            pair = (Input * 2)(down, up)
            if send(2, pair, ctypes.sizeof(Input)) != 2:
                release = (Input * 1)(up)
                send(1, release, ctypes.sizeof(Input))
                raise OSError("Unicode input incomplete; do not retry")

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0
    pyautogui.omni_natural = True
    pyautogui.omni_write = write_character
    return pyautogui
