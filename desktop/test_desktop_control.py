import unittest
from unittest.mock import Mock
from desktop_control import DesktopSession


class FakeBackend:
    class FailSafeException(Exception):
        pass
    KEYBOARD_KEYS = ["ctrl", "a", "enter", "shift"]
    def __init__(self):
        self.size = Mock(return_value=(1920, 1080))
        for name in ["moveTo", "click", "scroll", "press", "write", "keyDown", "keyUp", "mouseDown", "mouseUp", "screenshot"]:
            setattr(self, name, Mock())


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.now = 100
        self.session = DesktopSession(self.backend, "conversation", clock=lambda: self.now)
        self.token = self.session.credential()
    def run_action(self, action, args, token=None, conversation="conversation"):
        return self.session.execute(self.token if token is None else token, conversation, action, args)
    def test_token_required(self):
        with self.assertRaises(PermissionError): self.run_action("move", {"x": 5, "y": 5}, token="wrong")
        self.backend.size.assert_not_called()
    def test_conversation_bound(self):
        with self.assertRaises(PermissionError): self.run_action("screenshot", {}, conversation="other")
    def test_stopped(self):
        self.session.stop()
        with self.assertRaises(PermissionError): self.run_action("screenshot", {})
    def test_expired(self):
        self.now = 1000
        with self.assertRaises(PermissionError): self.run_action("screenshot", {})
    def test_move(self):
        self.run_action("move", {"x": 10, "y": 20})
        self.backend.moveTo.assert_called_once_with(10, 20)
    def test_coordinates(self):
        for x in [-1, 1920, True, 0.5]:
            with self.assertRaises(ValueError): self.run_action("move", {"x": x, "y": 20})
        self.backend.moveTo.assert_not_called()
    def test_click(self):
        self.run_action("click", {"x": 5, "y": 5, "button": "right"})
        self.backend.click.assert_called_once_with(5, 5, button="right")
    def test_schema(self):
        with self.assertRaises(ValueError): self.run_action("move", {"x": 1, "y": 2, "shell": "cmd"})
        with self.assertRaises(ValueError): self.run_action("shell", {})
    def test_scroll_limit(self):
        with self.assertRaises(ValueError): self.run_action("scroll", {"steps": 999})
        self.backend.scroll.assert_not_called()
    def test_hotkey_release(self):
        self.backend.keyDown.side_effect = [None, RuntimeError("injection")]
        with self.assertRaises(RuntimeError): self.run_action("hotkey", {"keys": ["ctrl", "a"]})
        self.backend.keyUp.assert_called_once_with("ctrl", _pause=False)
    def test_drag_release_after_stop(self):
        self.backend.moveTo.side_effect = lambda *args: self.session.stop() if self.backend.moveTo.call_count == 2 else None
        with self.assertRaises(PermissionError): self.run_action("drag", {"x": 1, "y": 1, "to_x": 50, "to_y": 50})
        self.backend.mouseUp.assert_called_once_with(_pause=False)
    def test_type_stop(self):
        self.backend.write.side_effect = lambda *args: self.session.stop()
        with self.assertRaises(PermissionError): self.run_action("type", {"text": "abc"})
        self.backend.write.assert_called_once_with("a")
    def test_unicode_rejected_not_silently_corrupted(self):
        with self.assertRaises(ValueError): self.run_action("type", {"text": "caffè"})
        self.backend.write.assert_not_called()
    def test_screenshot_memory(self):
        image = Mock(width=1920, height=1080)
        image.save.side_effect = lambda stream, format: stream.write(b"png-fixture")
        self.backend.screenshot.return_value = image
        result = self.run_action("screenshot", {})
        self.assertEqual(result["data"], b"png-fixture")
        self.assertEqual(result["mime"], "image/png")
    def test_failsafe_revokes(self):
        self.backend.moveTo.side_effect = self.backend.FailSafeException()
        with self.assertRaises(PermissionError): self.run_action("move", {"x": 1, "y": 1})
        with self.assertRaises(PermissionError): self.run_action("screenshot", {})


if __name__ == "__main__":
    unittest.main()
