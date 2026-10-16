import io
import json
import struct
import unittest
from unittest.mock import Mock
from native_channel import read_message, write_message, DesktopChannel, MAX_INPUT, MAX_OUTPUT
from native_host import validate_peer


class NativeTests(unittest.TestCase):
    def frame(self, raw):
        return io.BytesIO(struct.pack("=I", len(raw)) + raw)
    def test_roundtrip(self):
        stream = io.BytesIO()
        write_message(stream, {"ok": True, "text": "caffè"})
        stream.seek(0)
        self.assertEqual(read_message(stream), {"ok": True, "text": "caffè"})
    def test_clean_eof(self):
        self.assertIsNone(read_message(io.BytesIO()))
    def test_truncated(self):
        for raw in [b"x", struct.pack("=I", 5) + b"{}"]:
            with self.assertRaises(EOFError): read_message(io.BytesIO(raw))
    def test_input_limit(self):
        with self.assertRaises(ValueError): read_message(io.BytesIO(struct.pack("=I", MAX_INPUT + 1)))
    def test_duplicate_keys(self):
        with self.assertRaises(ValueError): read_message(self.frame(b'{"x":1,"x":2}'))
    def test_nonfinite(self):
        with self.assertRaises(ValueError): read_message(self.frame(b'{"x":NaN}'))
    def test_not_object(self):
        with self.assertRaises(ValueError): read_message(self.frame(b'[]'))
    def test_output_limit_no_partial_frame(self):
        stream = io.BytesIO()
        with self.assertRaises(ValueError): write_message(stream, {"text": "x" * MAX_OUTPUT})
        self.assertEqual(stream.getvalue(), b"")
    def channel(self):
        session = Mock()
        session.credential.return_value = "local-only"
        session.execute.return_value = {"status": "executed"}
        channel = DesktopChannel(session, "chat")
        req = {"session_id": channel.session_id, "sequence": 0, "action": "move", "args": {"x": 1, "y": 1}}
        return session, channel, req
    def test_replay_rejected(self):
        session, channel, req = self.channel()
        channel.handle(req)
        with self.assertRaises(PermissionError): channel.handle(req)
        session.execute.assert_called_once()
    def test_sequence_consumed_on_failure(self):
        session, channel, req = self.channel()
        session.execute.side_effect = RuntimeError("unknown effect")
        with self.assertRaises(RuntimeError): channel.handle(req)
        with self.assertRaises(PermissionError): channel.handle(req)
        session.execute.assert_called_once()
    def test_wrong_session(self):
        session, channel, req = self.channel()
        req["session_id"] = "other"
        with self.assertRaises(PermissionError): channel.handle(req)
        session.execute.assert_not_called()
    def test_screenshot_encoding(self):
        session, channel, req = self.channel()
        session.execute.return_value = {"data": b"png", "mime": "image/png"}
        result = channel.handle(req)
        self.assertEqual(result["result"]["data_base64"], "cG5n")
        self.assertNotIn("data", result["result"])
    def test_stop(self):
        session, channel, req = self.channel()
        channel.stop()
        session.stop.assert_called_once()
    def test_peer_validation(self):
        peer = "chrome-extension://" + "a" * 32 + "/"
        validate_peer(peer, peer)
        for bad in ["", "https://example.com/", "chrome-extension://" + "b" * 32 + "/"]:
            with self.assertRaises(PermissionError): validate_peer(bad, peer)


if __name__ == "__main__":
    unittest.main()
