"""Windows native host: visible local consent and STOP, no sockets."""
import os
import queue
import re
import sys
import threading
from native_channel import DesktopChannel, read_message, write_message
from native_bootstrap import initial_request


def validate_peer(peer, expected):
    pattern = r"chrome-extension://[a-p]{32}/"
    if not re.fullmatch(pattern, peer or "") or peer != expected:
        raise PermissionError("native extension origin not configured or mismatched")


def main():
    validate_peer(sys.argv[1] if len(sys.argv) > 1 else "",
                  os.environ.get("OMNINODE_NATIVE_ORIGIN", ""))
    if sys.platform != "win32":
        raise RuntimeError("desktop host supports Windows only")
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    first = initial_request(sys.stdin.buffer, sys.stdout.buffer)
    if first is None:
        return
    from desktop_control import DesktopSession, windows_backend
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title("OmniNode - desktop control")
    root.geometry("560x180")
    root.attributes("-topmost", True)
    state = {"channel": None, "blocked": False}
    events = queue.Queue()
    closed = threading.Event()
    label = tk.Label(root, text="Desktop OFF - waiting for authorized browser", wraplength=530)
    label.pack(padx=10, pady=15)

    def stop():
        state["blocked"] = True
        channel = state["channel"]
        if channel:
            channel.stop()
        label.configure(text="Desktop STOPPED - no new input allowed")

    def shutdown():
        stop()
        closed.set()
        root.destroy()

    tk.Button(root, text="STOP DESKTOP", command=stop, background="#b91c1c", foreground="white").pack(pady=10)
    root.protocol("WM_DELETE_WINDOW", shutdown)

    def pump():
        try:
            kind, data, done = events.get_nowait()
            if kind == "consent":
                allow = messagebox.askyesno("OmniNode desktop permission",
                    "Allow screen capture, mouse and keyboard for 10 minutes?\n\nConversation: " + data["conversation"], parent=root)
                if allow and not closed.is_set() and not state["blocked"]:
                    try:
                        session = DesktopSession(windows_backend(), data["conversation"])
                        state["channel"] = DesktopChannel(session, data["conversation"])
                        label.configure(text="Desktop ACTIVE (max 10 minutes) - " + data["conversation"])
                    except Exception:
                        label.configure(text="Desktop unavailable - backend initialization failed")
                done.set()
            elif kind == "closed":
                shutdown()
                return
        except queue.Empty:
            pass
        if not closed.is_set():
            root.after(50, pump)

    def worker():
        channel = None
        try:
            done = threading.Event()
            events.put(("consent", first, done))
            while not done.wait(0.1):
                if closed.is_set():
                    return
            channel = state["channel"]
            if channel is None:
                write_message(sys.stdout.buffer, {"ok": False, "error": "local consent absent or backend unavailable"})
                return
            write_message(sys.stdout.buffer, {"ok": True, "session_id": channel.session_id, "next_sequence": 0})
            while not closed.is_set():
                message = read_message(sys.stdin.buffer)
                if message is None:
                    return
                try:
                    result = channel.handle(message)
                    write_message(sys.stdout.buffer, {"ok": True, **result})
                except Exception:
                    channel.stop()
                    write_message(sys.stdout.buffer, {"ok": False, "error": "desktop operation failed; session stopped; do not retry input"})
                    return
        except Exception:
            try:
                write_message(sys.stdout.buffer, {"ok": False, "error": "native protocol or local desktop initialization failed"})
            except Exception:
                pass
        finally:
            if channel:
                channel.stop()
            closed.set()
            events.put(("closed", None, None))

    threading.Thread(target=worker, daemon=True).start()
    root.after(50, pump)
    root.mainloop()


if __name__ == "__main__":
    main()
