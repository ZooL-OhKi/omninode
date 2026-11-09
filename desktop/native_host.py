"""Windows native host: headless auto-consent mode, no GUI popups."""
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
    from windows_input_backend import configure_dpi
    configure_dpi()
    from desktop_control import DesktopSession, windows_backend

    channel = None
    try:
        session = DesktopSession(windows_backend(), first["conversation"], ttl=900)
        channel = DesktopChannel(session, first["conversation"])
        write_message(sys.stdout.buffer, {"ok": True, "session_id": channel.session_id, "next_sequence": 0})
        messages = queue.Queue()

        def reader():
            try:
                while True:
                    message = read_message(sys.stdin.buffer)
                    if message is None:
                        messages.put(None)
                        return
                    if isinstance(message, dict) and message.get("type") == "control" and message.get("command") == "STOP":
                        session.stop()
                        messages.put({"__control__": "STOP"})
                        return
                    messages.put(message)
            except Exception as exc:
                session.stop()
                messages.put(exc)

        reader_thread = threading.Thread(target=reader, daemon=True)
        reader_thread.start()
        while True:
            message = messages.get()
            if message is None:
                break
            if isinstance(message, Exception):
                raise message
            if isinstance(message, dict) and message.get("__control__") == "STOP":
                channel.stop()
                write_message(sys.stdout.buffer, {"ok": True, "stopped": True})
                break
            try:
                result = channel.handle(message)
                write_message(sys.stdout.buffer, {"ok": True, **result})
            except Exception as exc:
                channel.stop()
                write_message(sys.stdout.buffer, {"ok": False, "error": f"desktop operation failed: {exc}"})
                break
    except Exception as exc:
        try:
            write_message(sys.stdout.buffer, {"ok": False, "error": f"initialization failed: {exc}"})
        except Exception:
            pass
    finally:
        if channel:
            channel.stop()


if __name__ == "__main__":
    main()
