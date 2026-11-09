"""Deterministic, cooperative desktop backend. No listeners or anti-bot behavior."""
import hashlib
import io
import math
import sys
import time


def plan_eased_path(x0, y0, x1, y1, width, height, steps=20):
    values = (x0, y0, x1, y1, width, height, steps)
    if any(type(v) is not int for v in values) or width < 1 or height < 1 or not 1 <= steps <= 128:
        raise ValueError("invalid geometry")
    if not (0 <= x0 < width and 0 <= x1 < width and 0 <= y0 < height and 0 <= y1 < height):
        raise ValueError("point outside primary display")
    points = []
    for step in range(1, steps + 1):
        t = step / steps
        s = t * t * (3 - 2 * t)
        points.append((round(x0 + (x1 - x0) * s), round(y0 + (y1 - y0) * s)))
    return tuple(points)


def plan_typing_schedule(length, max_budget_sec=4.0):
    if type(length) is not int or not 1 <= length <= 256:
        raise ValueError("text limit exceeded")
    if not isinstance(max_budget_sec, (int, float)) or isinstance(max_budget_sec, bool) or not math.isfinite(max_budget_sec) or max_budget_sec <= 0:
        raise ValueError("invalid typing budget")
    schedule = (0.012,) * length
    if sum(schedule) > max_budget_sec:
        raise ValueError("typing schedule exceeds budget")
    return schedule


class WindowsInputBackend:
    def __init__(self, raw, natural=False, native=None):
        self.raw = raw
        self.natural = natural
        self.native = native
        self.target = None

    def size(self):
        return self.raw.size()

    def valid_key(self, key):
        return isinstance(key, str) and key in self.raw.KEYBOARD_KEYS

    def _release(self, items):
        active_error = sys.exc_info()[0] is not None
        errors = []
        for kind, value in reversed(items):
            try:
                if self.native:
                    self.native.release(kind, value)
                elif kind == "key":
                    self.raw.keyUp(value, _pause=False)
                else:
                    self.raw.mouseUp(_pause=False)
            except Exception as error:
                errors.append(error)
        if errors and not active_error:
            raise RuntimeError("input release incomplete; session must stop") from errors[0]

    def _focus(self, check, point=None):
        check()
        if self.native:
            if point is not None:
                self.target = self.native.target_at(*point)
            if self.target is None:
                raise PermissionError("select target with an explicitly confirmed click first")
            self.native.focus(self.target)
            self.native.await_ready(self.target)
        check()

    def _guard(self, check):
        check()
        if self.native:
            self.native.assert_focus(self.target)

    def _move(self, x, y, check, wait, guard_focus=False):
        if not self.natural:
            check()
            self.raw.moveTo(x, y)
            return
        start = self.raw.position()
        for px, py in plan_eased_path(int(start[0]), int(start[1]), x, y, *self.size()):
            if guard_focus:
                self._guard(check)
            else:
                check()
            self.raw.moveTo(px, py, _pause=False)
            wait(0.012)

    def perform(self, action, args, check, wait):
        b = self.raw
        check()
        if action == "screenshot":
            image = b.screenshot()
            if self.natural and (image.width, image.height) != tuple(self.size()):
                raise ValueError("screenshot and input geometry differ")
            stream = io.BytesIO()
            image.save(stream, format="PNG")
            check()
            return {"mime": "image/png", "width": image.width, "height": image.height, "data": stream.getvalue()}
        if action == "move":
            self._move(args["x"], args["y"], check, wait)
        elif action == "click":
            if not self.natural:
                b.click(args["x"], args["y"], button=args["button"])
            else:
                self._focus(check, (args["x"], args["y"]))
                self._move(args["x"], args["y"], check, wait, guard_focus=True)
                self._guard(check)
                try:
                    b.mouseDown(button=args["button"], _pause=False)
                    wait(0.040)
                finally:
                    self._release([("mouse", args["button"])])
        elif action == "drag":
            if self.natural:
                self._focus(check, (args["x"], args["y"]))
            self._move(args["x"], args["y"], check, wait, guard_focus=self.natural)
            check()
            try:
                b.mouseDown()
                if self.natural:
                    self._move(args["to_x"], args["to_y"], check, wait, guard_focus=True)
                else:
                    for step in range(1, 21):
                        check()
                        b.moveTo(round(args["x"] + (args["to_x"] - args["x"]) * step / 20), round(args["y"] + (args["to_y"] - args["y"]) * step / 20))
            finally:
                self._release([("mouse", "left")])
        elif action == "scroll":
            if self.natural:
                self._focus(check)
                for _ in range(abs(args["steps"])):
                    self._guard(check)
                    b.scroll(1 if args["steps"] > 0 else -1, _pause=False)
                    wait(0.035)
            else:
                b.scroll(args["steps"])
        elif action == "type":
            if self.natural:
                schedule = plan_typing_schedule(len(args["text"]))
                self._focus(check)
                for char, delay in zip(args["text"], schedule):
                    self._guard(check)
                    b.omni_write(char)
                    wait(delay)
            else:
                for char in args["text"]:
                    check()
                    b.write(char)
        elif action in {"press", "hotkey"}:
            keys = [args["key"]] if action == "press" else args["keys"]
            if not self.natural and action == "press":
                b.press(args["key"])
            else:
                if self.natural:
                    self._focus(check)
                held = []
                try:
                    for key in keys:
                        self._guard(check)
                        if self.natural:
                            held.append(("key", key))
                        b.keyDown(key)
                        if not self.natural:
                            held.append(("key", key))
                        if self.natural:
                            wait(0.025)
                finally:
                    self._release(held)
        else:
            raise ValueError("unsupported action")
        check()
        return {"status": "executed", "action": action}


def configure_dpi():
    import ctypes
    from ctypes import wintypes
    user = ctypes.WinDLL("user32", use_last_error=True)
    setter = user.SetProcessDpiAwarenessContext
    setter.argtypes = [wintypes.HANDLE]
    setter.restype = wintypes.BOOL
    getter = user.GetThreadDpiAwarenessContext
    getter.restype = wintypes.HANDLE
    awareness = user.GetAwarenessFromDpiAwarenessContext
    awareness.argtypes = [wintypes.HANDLE]
    awareness.restype = ctypes.c_int
    setter(ctypes.c_void_p(-4))
    if awareness(getter()) != 2:
        raise RuntimeError("per-monitor DPI awareness unavailable; desktop disabled")


def make_windows_backend():
    if sys.platform != "win32":
        raise RuntimeError("native backend supports Windows only")
    import ctypes
    from ctypes import wintypes as w
    import pyautogui as raw

    class MI(ctypes.Structure):
        _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD), ("dwFlags", w.DWORD), ("time", w.DWORD), ("extra", ctypes.c_size_t)]

    class KI(ctypes.Structure):
        _fields_ = [("vk", w.WORD), ("scan", w.WORD), ("flags", w.DWORD), ("time", w.DWORD), ("extra", ctypes.c_size_t)]

    class HI(ctypes.Structure):
        _fields_ = [("msg", w.DWORD), ("low", w.WORD), ("high", w.WORD)]

    class U(ctypes.Union):
        _fields_ = [("mi", MI), ("ki", KI), ("hi", HI)]

    class Input(ctypes.Structure):
        _anonymous_ = ("data",)
        _fields_ = [("type", w.DWORD), ("data", U)]

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", w.DWORD),
            ("flags", w.DWORD),
            ("hwndActive", w.HWND),
            ("hwndFocus", w.HWND),
            ("hwndCapture", w.HWND),
            ("hwndMenuOwner", w.HWND),
            ("hwndMoveSize", w.HWND),
            ("hwndCaret", w.HWND),
            ("rcCaret", w.RECT),
        ]

    user = ctypes.WinDLL("user32", use_last_error=True)
    user.SendInput.argtypes = [w.UINT, ctypes.POINTER(Input), ctypes.c_int]
    user.SendInput.restype = w.UINT
    user.GetForegroundWindow.restype = w.HWND
    user.WindowFromPoint.argtypes = [w.POINT]
    user.WindowFromPoint.restype = w.HWND
    user.GetAncestor.argtypes = [w.HWND, w.UINT]
    user.GetAncestor.restype = w.HWND
    user.SetForegroundWindow.argtypes = [w.HWND]
    user.SetForegroundWindow.restype = w.BOOL
    user.IsWindow.argtypes = [w.HWND]
    user.IsWindow.restype = w.BOOL
    user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
    user.GetWindowThreadProcessId.restype = w.DWORD
    user.GetGUIThreadInfo.argtypes = [w.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user.GetGUIThreadInfo.restype = w.BOOL
    user.GetClassNameW.argtypes = [w.HWND, ctypes.c_wchar_p, ctypes.c_int]
    user.GetClassNameW.restype = ctypes.c_int
    user.GetWindowRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
    user.GetWindowRect.restype = w.BOOL
    user.SendMessageTimeoutW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM, w.UINT, w.UINT, ctypes.POINTER(w.DWORD_PTR)]
    user.SendMessageTimeoutW.restype = w.BOOL

    class Native:
        def emit(self, entries):
            packet = (Input * len(entries))(*entries)
            if user.SendInput(len(entries), packet, ctypes.sizeof(Input)) != len(entries):
                raise OSError("input incomplete; do not retry")

        def identity(self, hwnd):
            if not hwnd or not user.IsWindow(hwnd):
                raise PermissionError("target window unavailable")
            pid = w.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                raise PermissionError("target process unavailable")
            return (int(hwnd), pid.value)

        def _thread_of(self, hwnd):
            pid = w.DWORD()
            thread = user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not thread or not pid.value:
                raise PermissionError("target thread unavailable")
            return int(thread), int(pid.value)

        def _gui(self, thread):
            info = GUITHREADINFO()
            info.cbSize = ctypes.sizeof(info)
            if not user.GetGUIThreadInfo(thread, ctypes.byref(info)):
                raise PermissionError("target thread unavailable")
            return info

        def _window_signature(self, hwnd):
            cls = ctypes.create_unicode_buffer(256)
            if not user.GetClassNameW(hwnd, cls, 256):
                raise PermissionError("target class unavailable")
            rect = w.RECT()
            if not user.GetWindowRect(hwnd, ctypes.byref(rect)):
                raise PermissionError("target geometry unavailable")
            payload = (cls.value + "|" + str(rect.left) + "," + str(rect.top) + "," + str(rect.right) + "," + str(rect.bottom)).encode("utf-16-le")
            return hashlib.sha256(payload).hexdigest()

        def _rich_identity(self, hwnd):
            base = self.identity(hwnd)
            thread, pid = self._thread_of(hwnd)
            info = self._gui(thread)
            focus = int(info.hwndFocus or 0)
            if not focus or not user.IsWindow(focus):
                raise PermissionError("target focus unavailable")
            focus_pid = w.DWORD()
            focus_thread = user.GetWindowThreadProcessId(focus, ctypes.byref(focus_pid))
            if not focus_pid.value or focus_pid.value != pid or focus_thread != thread:
                raise PermissionError("target focus belongs to another thread")
            return (base[0], focus, thread, pid, self._window_signature(focus))

        def target_at(self, x, y):
            hwnd = user.GetAncestor(user.WindowFromPoint(w.POINT(x, y)), 2)
            return self._rich_identity(hwnd)

        def assert_focus(self, target):
            if target is None:
                raise PermissionError("select target with an explicitly confirmed click first")
            if self._rich_identity(target[0]) != target:
                raise PermissionError("target identity or focus changed; no input delivered")
            if int(user.GetForegroundWindow() or 0) != target[0]:
                raise PermissionError("target focus changed; no input delivered")

        def focus(self, target):
            if self._rich_identity(target[0]) != target:
                raise PermissionError("target identity changed")
            if int(user.GetForegroundWindow() or 0) != target[0]:
                user.SetForegroundWindow(target[0])
            self.assert_focus(target)

        def await_ready(self, target, timeout_ms=500):
            deadline = time.monotonic() + max(timeout_ms, 0) / 1000.0
            last = None
            while time.monotonic() < deadline:
                self.assert_focus(target)
                info = self._gui(target[2])
                state = (int(info.hwndFocus or 0), int(info.hwndActive or 0), int(info.hwndCapture or 0))
                if state == last:
                    result = w.DWORD_PTR()
                    if not user.SendMessageTimeoutW(target[0], 0, 0, 0, 2, 250, ctypes.byref(result)):
                        raise PermissionError("target message loop unavailable; no input delivered")
                    return True
                last = state
                time.sleep(0.025)
            raise PermissionError("target not stable; no input delivered")

        def release(self, kind, value):
            if kind == "mouse":
                flags = {"left": 4, "right": 16, "middle": 64}[value]
                self.emit([Input(type=0, mi=MI(dwFlags=flags))])
            else:
                code = raw.platformModule.keyboardMapping.get(value)
                if not isinstance(code, int):
                    raise ValueError("unknown release key")
                flags = 2 | (1 if value in {"left", "right", "up", "down", "home", "end", "pageup", "pagedown", "insert", "delete", "win", "winleft", "winright", "ctrlright", "altright"} else 0)
                self.emit([Input(type=1, ki=KI(vk=code & 255, flags=flags))])

        def write(self, char):
            raw.failSafeCheck()
            encoded = char.encode("utf-16-le", errors="strict")
            units = [int.from_bytes(encoded[i:i + 2], "little") for i in range(0, len(encoded), 2)]
            events = []
            for unit in units:
                events.append(Input(type=1, ki=KI(scan=unit, flags=4)))
                events.append(Input(type=1, ki=KI(scan=unit, flags=6)))
            if not events:
                raise ValueError("empty character")
            self.emit(events)

    native = Native()
    raw.FAILSAFE = True
    raw.PAUSE = 0
    raw.omni_write = native.write
    return WindowsInputBackend(raw, natural=True, native=native)
