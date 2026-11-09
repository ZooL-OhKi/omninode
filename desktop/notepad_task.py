"""Single approved Notepad goal. No generic shell or input replay."""
import os


def verify_notepad_process(target):
    import ctypes
    from ctypes import wintypes as w
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    handle = kernel.OpenProcess(0x1000, False, target[1])
    if not handle:
        raise PermissionError("cannot verify target process")
    try:
        text = ctypes.create_unicode_buffer(32768)
        length = w.DWORD(len(text))
        if not kernel.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(length)):
            raise PermissionError("cannot verify target image")
        path = os.path.normcase(os.path.abspath(text.value))
        windows = os.path.normcase(os.path.abspath(os.environ["WINDIR"]))
        apps = os.path.normcase(os.path.abspath(os.path.join(os.environ["ProgramFiles"], "WindowsApps"))) + os.sep
        classic = {os.path.normcase(os.path.join(windows, "notepad.exe")), os.path.normcase(os.path.join(windows, "System32", "notepad.exe"))}
        if os.path.basename(path) != "notepad.exe" or not (path in classic or path.startswith(apps + "microsoft.windowsnotepad_")):
            raise PermissionError("goal is restricted to Windows Notepad")
    finally:
        kernel.CloseHandle(handle)


def run_notepad_write(backend, args, check, wait, verifier=None):
    from windows_input_backend import WindowsInputBackend
    if not backend.natural or backend.native is None:
        raise PermissionError("verified native backend required")
    if not isinstance(args, dict) or set(args) != {"x", "y", "text"}:
        raise ValueError("invalid task schema")
    width, height = backend.size()
    x, y, text = args["x"], args["y"], args["text"]
    if type(x) is not int or type(y) is not int or not (0 <= x < width and 0 <= y < height):
        raise ValueError("point outside primary display")
    if not isinstance(text, str) or not 1 <= len(text) <= 256 or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xd800 <= ord(c) <= 0xdfff for c in text):
        raise ValueError("invalid task text")
    check()
    original = backend.native
    target = original.target_at(x, y)
    (verify_notepad_process if verifier is None else verifier)(target)
    check()

    class Guard:
        def target_at(self, px, py):
            current = original.target_at(px, py)
            if current != target:
                raise PermissionError("task target changed")
            return current

        def focus(self, current):
            if current != target:
                raise PermissionError("task target changed")
            original.focus(target)

        def assert_focus(self, current):
            if current != target:
                raise PermissionError("task target changed")
            original.assert_focus(target)

        def release(self, kind, value):
            original.release(kind, value)

    executor = WindowsInputBackend(backend.raw, natural=True, native=Guard())
    executor.perform("click", {"x": x, "y": y, "button": "left"}, check, wait)
    check()
    executor.perform("type", {"text": text}, check, wait)
    check()
    return {"status": "executed", "action": "notepad_write", "typed_characters": len(text)}
