import io
import json
import unittest
from PIL import Image
from screen_preview import compact_screenshot, MAX_PREVIEW, MAX_SOURCE
from native_channel import DesktopChannel, write_message, MAX_OUTPUT
from unittest.mock import Mock


class ScreenTests(unittest.TestCase):
    def source(self):
        data = bytes((i * 37 + (i >> 7) * 11) % 256 for i in range(1600 * 900 * 3))
        image = Image.frombytes("RGB", (1600, 900), data)
        stream = io.BytesIO()
        image.save(stream, format="BMP")
        return {"data": stream.getvalue(), "mime": "image/bmp", "width": 1600, "height": 900}
    def test_small_payload_preserved(self):
        data = {"data": b"small-fixture", "mime": "image/png", "width": 1, "height": 1}
        self.assertEqual(compact_screenshot(data), data)
    def test_large_preview_real_image(self):
        result = compact_screenshot(self.source())
        self.assertEqual(result["mime"], "image/jpeg")
        self.assertLessEqual(len(result["data"]), MAX_PREVIEW)
        self.assertEqual((result["width"], result["height"]), (1600, 900))
        image = Image.open(io.BytesIO(result["data"]))
        self.assertEqual(image.size, (result["preview_width"], result["preview_height"]))
        self.assertLessEqual(image.width, 1280)
    def test_original_not_mutated(self):
        original = self.source()
        mime = original["mime"]
        compact_screenshot(original)
        self.assertEqual(original["mime"], mime)
    def test_dimension_mismatch(self):
        data = self.source()
        data["width"] = 10
        with self.assertRaises(ValueError): compact_screenshot(data)
    def test_invalid_image(self):
        with self.assertRaises(Exception): compact_screenshot({"data": b"x" * (MAX_PREVIEW + 1)})
    def test_source_cap(self):
        with self.assertRaises(ValueError): compact_screenshot({"data": b"x" * (MAX_SOURCE + 1)})
    def test_native_frame_with_real_preview(self):
        session = Mock()
        session.credential.return_value = "local"
        session.execute.return_value = self.source()
        channel = DesktopChannel(session, "chat")
        result = channel.handle({"session_id":channel.session_id, "sequence":0,"action":"screenshot","args":{}})
        stream = io.BytesIO()
        write_message(stream, {"ok": True, **result})
        self.assertLessEqual(len(stream.getvalue()) - 4, MAX_OUTPUT)
        self.assertEqual(result["result"]["mime"], "image/jpeg")


if __name__ == "__main__":
    unittest.main()
