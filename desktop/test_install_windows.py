import unittest
from unittest.mock import patch
from install_windows import build_plan, checked_path, apply_plan


class InstallTests(unittest.TestCase):
    def plan(self, **kwargs):
        return build_plan(kwargs.get("source", "C:/repo/desktop"), kwargs.get("base", "C:/Users/test/AppData/Local/OmniNode/NativeHost-chrome"), kwargs.get("extension_id", "a" * 32), kwargs.get("browser", "chrome"))
    def test_exact_origin_only(self):
        self.assertEqual(self.plan()["manifest"]["allowed_origins"], ["chrome-extension://" + "a" * 32 + "/"])
    def test_native_name(self):
        self.assertEqual(self.plan()["manifest"]["name"], "com.omninode.desktop")
    def test_user_registry_path(self):
        self.assertEqual(self.plan()["registry"], "Software\\Google\\Chrome\\NativeMessagingHosts\\com.omninode.desktop")
    def test_edge_registry_path(self):
        self.assertIn("Microsoft\\Edge", self.plan(browser="edge")["registry"])
    def test_launcher_uses_isolated_runtime(self):
        p = self.plan(source="C:/my repo/desktop")
        self.assertIn('"' + p["python"] + '" -u "C:\\my repo\\desktop\\native_host.py" %*', p["launcher"])
        self.assertIn('OMNINODE_NATIVE_ORIGIN=chrome-extension://', p["launcher"])
    def test_extension_id(self):
        for value in ["", "a" * 31, "z" * 32, "a" * 32 + "&cmd"]:
            with self.assertRaises(ValueError): self.plan(extension_id=value)
    def test_provider(self):
        with self.assertRaises(ValueError): self.plan(browser="other")
    def test_path_injection(self):
        for value in ["relative", "C:/repo&cmd", "C:/%USERPROFILE%/repo", "C:/repo!/x", "C:/repo\ncmd", "C:/repo/../other", "//server/share/repo", "C:/utentè/repo"]:
            with self.assertRaises(ValueError): checked_path(value)
    def test_apply_not_run_on_nonwindows(self):
        with patch("install_windows.sys.platform", "linux"):
            with self.assertRaises(RuntimeError): apply_plan(self.plan())


if __name__ == "__main__":
    unittest.main()
