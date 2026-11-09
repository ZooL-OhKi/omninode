import io
import struct
import unittest
from native_bootstrap import initial_request
from native_channel import read_message, write_message


class StartupTests(unittest.TestCase):
    def invoke(self, request):
        source = io.BytesIO()
        write_message(source, request)
        source.seek(0)
        output = io.BytesIO()
        result = initial_request(source, output)
        output.seek(0)
        return result, read_message(output)
    def test_ping_has_no_grant_or_credential(self):
        result, response = self.invoke({"type": "ping"})
        self.assertIsNone(result)
        self.assertEqual(response, {"ok": True, "protocol": 1, "desktop_active": False, "consent_required": True})
    def test_open_only_returns_request_for_consent(self):
        request = {"type": "open", "conversation": "https://www.perplexity.ai/search/fixture"}
        result, response = self.invoke(request)
        self.assertEqual(result, request)
        self.assertIsNone(response)
    def test_extra_fields_never_authorize(self):
        for request in [{"type":"ping","action":"click"}, {"type":"open","conversation":"chat","approved":True}]:
            result, response = self.invoke(request)
            self.assertIsNone(result)
            self.assertFalse(response["ok"])
    def test_invalid_conversation(self):
        for text in ["", "x"*1025, "line\nbreak", "bad\x7ftext", "\ud800"]:
            result, response = self.invoke({"type":"open","conversation":text})
            self.assertIsNone(result)
            self.assertFalse(response["ok"])
    def test_truncated_or_invalid_json(self):
        for raw in [b"x", struct.pack("=I",3)+b"abc"]:
            output=io.BytesIO()
            self.assertIsNone(initial_request(io.BytesIO(raw),output))
            output.seek(0)
            self.assertFalse(read_message(output)["ok"])
    def test_empty_input_does_not_create_session(self):
        output=io.BytesIO()
        self.assertIsNone(initial_request(io.BytesIO(),output))
        self.assertEqual(output.getvalue(),b"")
    def test_ping_does_not_consume_following_open(self):
        source=io.BytesIO()
        write_message(source,{"type":"ping"})
        write_message(source,{"type":"open","conversation":"not authorized"})
        source.seek(0)
        self.assertIsNone(initial_request(source,io.BytesIO()))
        self.assertEqual(read_message(source),{"type":"open","conversation":"not authorized"})


if __name__ == "__main__":
    unittest.main()
