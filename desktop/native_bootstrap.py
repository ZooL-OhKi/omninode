"""Read-only startup probe; only open requests may reach local consent."""
from native_channel import read_message, write_message


def initial_request(source, destination):
    try:
        request = read_message(source)
        if request is None:
            return None
        if request == {"type": "ping"}:
            write_message(destination, {"ok": True, "protocol": 1,
                                       "desktop_active": False, "consent_required": True})
            return None
        if (set(request) != {"type", "conversation"} or request["type"] != "open"
                or not isinstance(request["conversation"], str)
                or not 1 <= len(request["conversation"]) <= 1024
                or any(ord(c) < 32 or ord(c) == 127 for c in request["conversation"])):
            raise ValueError("invalid first request")
        request["conversation"].encode("utf-8", errors="strict")
        return request
    except (ValueError, EOFError, UnicodeError):
        write_message(destination, {"ok": False, "error": "invalid native startup request"})
        return None
