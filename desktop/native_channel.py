"""Native Messaging framing and desktop session dispatch; no network listener."""
import base64
import json
import secrets
import struct
from screen_preview import compact_screenshot

MAX_INPUT = 131072
MAX_OUTPUT = 1048576


def _exact(stream, size):
    parts = bytearray()
    while len(parts) < size:
        chunk = stream.read(size - len(parts))
        if not chunk:
            raise EOFError("truncated native frame")
        parts.extend(chunk)
    return bytes(parts)


def _object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def read_message(stream):
    first = stream.read(1)
    if not first:
        return None
    length = struct.unpack("=I", first + _exact(stream, 3))[0]
    if not 1 <= length <= MAX_INPUT:
        raise ValueError("native input size limit")
    def reject_constant(value):
        raise ValueError("non-finite JSON value")
    value = json.loads(_exact(stream, length).decode("utf-8"),
                       object_pairs_hook=_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("native message must be object")
    return value


def write_message(stream, message):
    raw = json.dumps(message, ensure_ascii=True, allow_nan=False).encode("utf-8")
    if len(raw) > MAX_OUTPUT:
        raise ValueError("native output size limit")
    stream.write(struct.pack("=I", len(raw)) + raw)
    stream.flush()


class DesktopChannel:
    """Local grant must already exist. Never approves a browser request itself."""
    def __init__(self, session, conversation):
        self.session = session
        self.conversation = conversation
        self.session_id = secrets.token_urlsafe(24)
        self.sequence = 0

    def handle(self, request):
        if (set(request) != {"session_id", "sequence", "action", "args"}
                or request["session_id"] != self.session_id
                or type(request["sequence"]) is not int
                or request["sequence"] != self.sequence):
            raise PermissionError("invalid desktop channel or sequence; do not retry input")
        self.sequence += 1
        result = self.session.execute(self.session.credential(), self.conversation,
                                      request["action"], request["args"])
        if isinstance(result, dict) and isinstance(result.get("data"), bytes):
            result = compact_screenshot(result)
            result["data_base64"] = base64.b64encode(result.pop("data")).decode("ascii")
        return {"session_id": self.session_id, "sequence": request["sequence"], "result": result}

    def stop(self):
        self.session.stop()
