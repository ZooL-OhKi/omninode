import unittest
from unittest.mock import Mock, patch
from notepad_task import run_notepad_write


class TaskTests(unittest.TestCase):
    def fixture(self):
        backend = Mock()
        backend.natural = True
        backend.size.return_value = (1920, 1080)
        backend.native.target_at.return_value = (10, 20)
        return backend, {"x": 300, "y": 300, "text": "OmniNode operativo: caffè."}

    def test_exact_two_step_plan(self):
        backend, args = self.fixture()
        executor = Mock()
        with patch("windows_input_backend.WindowsInputBackend", return_value=executor):
            result = run_notepad_write(backend, args, lambda: None, lambda n: None, lambda target: None)
        self.assertEqual([c.args[0] for c in executor.perform.call_args_list], ["click", "type"])
        self.assertEqual(executor.perform.call_args_list[1].args[1], {"text": args["text"]})
        self.assertEqual(result["action"], "notepad_write")

    def test_rejects_other_application_before_input(self):
        backend, args = self.fixture()
        with patch("windows_input_backend.WindowsInputBackend") as factory:
            with self.assertRaises(PermissionError):
                run_notepad_write(backend, args, lambda: None, lambda n: None, Mock(side_effect=PermissionError("not Notepad")))
            factory.assert_not_called()

    def test_rejects_bad_text_before_input(self):
        for value in ("", "x" * 257, "hello\nworld", "\ud800"):
            backend, args = self.fixture()
            args["text"] = value
            with self.assertRaises(ValueError):
                run_notepad_write(backend, args, lambda: None, lambda n: None, lambda target: None)
            backend.native.target_at.assert_not_called()

    def test_stop_between_steps(self):
        backend, args = self.fixture()
        executor = Mock()
        stopped = [False]
        executor.perform.side_effect = lambda *a: stopped.__setitem__(0, True)
        def check():
            if stopped[0]:
                raise PermissionError("STOP")
        with patch("windows_input_backend.WindowsInputBackend", return_value=executor):
            with self.assertRaises(PermissionError):
                run_notepad_write(backend, args, check, lambda n: None, lambda target: None)
        self.assertEqual(executor.perform.call_count, 1)

    def test_typing_failure_is_not_retried(self):
        backend, args = self.fixture()
        executor = Mock()
        executor.perform.side_effect = [None, RuntimeError("uncertain")]
        with patch("windows_input_backend.WindowsInputBackend", return_value=executor):
            with self.assertRaises(RuntimeError):
                run_notepad_write(backend, args, lambda: None, lambda n: None, lambda target: None)
        self.assertEqual(executor.perform.call_count, 2)

    def test_target_switch_is_rejected(self):
        backend, args = self.fixture()
        backend.native.target_at.side_effect = [(10, 20), (11, 21)]
        def factory(raw, natural, native):
            native.target_at(300, 300)
        with patch("windows_input_backend.WindowsInputBackend", side_effect=factory):
            with self.assertRaises(PermissionError):
                run_notepad_write(backend, args, lambda: None, lambda n: None, lambda target: None)
