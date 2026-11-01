import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from desktop_control import DesktopSession
from windows_input_backend import WindowsInputBackend, plan_eased_path, plan_typing_schedule


class Raw:
    class FailSafeException(Exception):
        pass
    KEYBOARD_KEYS = ["ctrl", "a", "enter"]
    def __init__(self):
        self.size = Mock(return_value=(1920, 1080))
        self.position = Mock(return_value=(100, 100))
        for name in ("moveTo", "mouseDown", "mouseUp", "keyDown", "keyUp", "omni_write", "scroll"):
            setattr(self, name, Mock())


class BackendTests(unittest.TestCase):
    def test_path_bounds_endpoint_and_repeatability(self):
        for start, end in (((0, 0), (1919, 1079)), ((1919, 0), (0, 1079)), ((5, 5), (5, 5))):
            path = plan_eased_path(*start, *end, 1920, 1080)
            self.assertEqual(path, plan_eased_path(*start, *end, 1920, 1080))
            self.assertEqual(path[-1], end)
            self.assertTrue(all(0 <= x < 1920 and 0 <= y < 1080 for x, y in path))
    def test_invalid_points(self):
        for x in (-1, 1920, True, 0.5):
            with self.assertRaises(ValueError):
                plan_eased_path(0, 0, x, 2, 1920, 1080)
    def test_typing_budget(self):
        self.assertLess(sum(plan_typing_schedule(256)), 3.5)
        for n in (0, 257, True):
            with self.assertRaises(ValueError):
                plan_typing_schedule(n)
        with self.assertRaises(ValueError):
            plan_typing_schedule(256, 1.0)
    def test_stop_during_move(self):
        raw = Raw()
        session = DesktopSession(WindowsInputBackend(raw, natural=True), "conversation")
        raw.moveTo.side_effect = lambda *a, **k: session.stop()
        with self.assertRaises(PermissionError):
            session.execute(session.credential(), "conversation", "move", {"x": 200, "y": 200})
        self.assertEqual(raw.moveTo.call_count, 1)
    def test_stop_releases_drag(self):
        raw = Raw()
        session = DesktopSession(WindowsInputBackend(raw, natural=True), "conversation")
        raw.mouseDown.side_effect = session.stop
        with self.assertRaises(PermissionError):
            session.execute(session.credential(), "conversation", "drag", {"x": 110, "y": 110, "to_x": 200, "to_y": 200})
        raw.mouseUp.assert_called_once_with(_pause=False)
    def test_stop_releases_hotkey(self):
        raw = Raw()
        session = DesktopSession(WindowsInputBackend(raw, natural=True), "conversation")
        raw.keyDown.side_effect = lambda *a, **k: session.stop()
        with self.assertRaises(PermissionError):
            session.execute(session.credential(), "conversation", "hotkey", {"keys": ["ctrl", "a"]})
        raw.keyUp.assert_called_once_with("ctrl", _pause=False)
    def test_deadline_stops_partial_type(self):
        raw = Raw()
        now = [0.0]
        session = DesktopSession(WindowsInputBackend(raw, natural=True), "conversation", clock=lambda: now[0])
        raw.omni_write.side_effect = lambda *a: now.__setitem__(0, 13.0)
        with self.assertRaises(TimeoutError):
            session.execute(session.credential(), "conversation", "type", {"text": "abc"})
        self.assertEqual(raw.omni_write.call_count, 1)
        with self.assertRaises(PermissionError):
            session.execute(session.credential(), "conversation", "move", {"x": 1, "y": 1})
    def test_partial_keydown_attempt_is_released(self):
        raw = Raw()
        raw.keyDown.side_effect = RuntimeError("uncertain input")
        backend = WindowsInputBackend(raw, natural=True)
        with self.assertRaises(RuntimeError):
            backend.perform("hotkey", {"keys": ["ctrl"]}, lambda: None, lambda n: None)
        raw.keyUp.assert_called_once_with("ctrl", _pause=False)
    def test_release_attempts_all_keys(self):
        raw = Raw()
        raw.keyUp.side_effect = RuntimeError("failed release")
        with self.assertRaises(RuntimeError):
            WindowsInputBackend(raw)._release([("key", "ctrl"), ("key", "a")])
        self.assertEqual(raw.keyUp.call_count, 2)
    def test_native_typing_requires_target(self):
        raw = Raw()
        native = Mock(spec=["assert_focus", "focus", "release"])
        with self.assertRaises(PermissionError):
            WindowsInputBackend(raw, natural=True, native=native).perform("type", {"text": "abc"}, lambda: None, lambda n: None)
        raw.omni_write.assert_not_called()
    def test_focus_checked_each_character(self):
        raw = Raw()
        native = Mock(spec=["assert_focus", "focus", "release"])
        native.assert_focus.side_effect = [None, PermissionError("focus changed")]
        backend = WindowsInputBackend(raw, natural=True, native=native)
        backend.target = (1, 2)
        with self.assertRaises(PermissionError):
            backend.perform("type", {"text": "abc"}, lambda: None, lambda n: None)
        self.assertEqual(raw.omni_write.call_count, 1)

    def test_focus_change_during_drag_releases(self):
        raw = Raw()
        native = Mock(spec=["assert_focus", "focus", "release", "target_at"])
        native.target_at.return_value = (1, 2)
        native.assert_focus.side_effect = [None] * 20 + [PermissionError("focus changed")]
        backend = WindowsInputBackend(raw, natural=True, native=native)
        with self.assertRaises(PermissionError):
            backend.perform("drag", {"x": 110, "y": 110, "to_x": 200, "to_y": 200}, lambda: None, lambda n: None)
        native.release.assert_called_once_with("mouse", "left")


class InstallerSourceTests(unittest.TestCase):
    def test_complete_source(self):
        from install_windows import REQUIRED_SOURCE_FILES, validate_source
        with tempfile.TemporaryDirectory() as folder:
            for name in REQUIRED_SOURCE_FILES:
                (Path(folder) / name).write_text("fixture", encoding="utf-8")
            validate_source(folder)
    def test_missing_backend(self):
        from install_windows import REQUIRED_SOURCE_FILES, validate_source
        with tempfile.TemporaryDirectory() as folder:
            for name in REQUIRED_SOURCE_FILES:
                if name != "windows_input_backend.py":
                    (Path(folder) / name).write_text("fixture", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                validate_source(folder)
    def test_linked_backend(self):
        from install_windows import REQUIRED_SOURCE_FILES, validate_source
        with tempfile.TemporaryDirectory() as folder:
            for name in REQUIRED_SOURCE_FILES:
                (Path(folder) / name).write_text("fixture", encoding="utf-8")
            backend = Path(folder) / "windows_input_backend.py"
            backend.unlink()
            try:
                backend.symlink_to(Path(folder) / "desktop_control.py")
            except OSError as error:
                self.skipTest(str(error))
            with self.assertRaises(ValueError):
                validate_source(folder)
