"""Opt-in Windows setup/launcher test; never enables desktop input."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import uuid
from install_windows import build_plan, apply_plan


@unittest.skipUnless(sys.platform == "win32" and os.environ.get("OMNINODE_WINDOWS_SETUP_TEST") == "1", "opt-in disposable Windows setup test")
class WindowsSetupSmoke(unittest.TestCase):
    def test_isolated_install_and_real_launcher_ping(self):
        import winreg
        with tempfile.TemporaryDirectory(prefix="omninode-ci-") as folder:
            plan = build_plan(Path(__file__).resolve().parent, Path(folder) / "native host", "a" * 32)
            # Actual registry APIs, isolated test key; never Chrome/Edge registration.
            plan["registry"] = "Software\\OmniNodeCI\\" + uuid.uuid4().hex
            try:
                apply_plan(plan)
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, plan["registry"]) as key:
                    self.assertEqual(winreg.QueryValueEx(key, "")[0], plan["manifest_path"])
                manifest = json.loads(Path(plan["manifest_path"]).read_text(encoding="utf-8"))
                self.assertEqual(manifest["allowed_origins"], [plan["origin"]])
                check = subprocess.run([plan["python"], "-c", "import importlib.util,json; print(json.dumps({p:importlib.util.find_spec(p) is not None for p in ('pyautogui','PIL','tkinter','_tkinter')}))"], capture_output=True, text=True, timeout=30, check=True)
                self.assertTrue(all(json.loads(check.stdout).values()))
                body = json.dumps({"type":"ping"}).encode()
                body += b" " * (26 - len(body))
                packet = struct.pack("=I", len(body)) + body
                self.assertEqual(packet[0], 26)  # Ctrl-Z exercises Windows binary pipe mode.
                comspec = os.environ["COMSPEC"]
                def launch(origin):
                    command = '"' + comspec + '" /d /s /c ""' + manifest["path"] + '" "' + origin + '""'
                    return subprocess.run(command, executable=comspec, input=packet, capture_output=True, timeout=30)
                response = launch(plan["origin"])
                self.assertEqual(response.returncode, 0, response.stderr.decode(errors="replace"))
                self.assertGreaterEqual(len(response.stdout), 4)
                size = struct.unpack("=I", response.stdout[:4])[0]
                self.assertEqual(len(response.stdout), size + 4)
                self.assertEqual(json.loads(response.stdout[4:]), {"ok":True,"protocol":1,"desktop_active":False,"consent_required":True})
                denied = launch("chrome-extension://" + "b" * 32 + "/")
                self.assertNotEqual(denied.returncode, 0)
                self.assertEqual(denied.stdout, b"")
            finally:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, plan["registry"]) as key:
                        owned = winreg.QueryValueEx(key, "")[0] == plan["manifest_path"]
                    if owned:
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, plan["registry"])
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    unittest.main()
