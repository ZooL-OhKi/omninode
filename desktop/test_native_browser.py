"""Real Chromium native pipe with a synthetic image host, never a real desktop."""
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import sys
import sysconfig
import tempfile
import unittest

HOST_SCRIPT = r"""import io, sys
from PIL import Image
from native_channel import read_message, write_message, DesktopChannel
class FixtureSession:
    def credential(self): return "fixture-only"
    def stop(self): pass
    def execute(self, token, conversation, action, args):
        if token != "fixture-only" or conversation != "fixture" or action != "screenshot" or args != {}:
            raise PermissionError("fixture only")
        image = Image.effect_noise((1600,900), 100).convert("RGB")
        stream = io.BytesIO(); image.save(stream, format="PNG")
        return {"data":stream.getvalue(),"mime":"image/png","width":1600,"height":900}
first = read_message(sys.stdin.buffer)
if first != {"type":"open","conversation":"fixture"}: raise PermissionError("fixture binding")
channel = DesktopChannel(FixtureSession(), "fixture")
write_message(sys.stdout.buffer, {"ok":True,"session_id":channel.session_id,"next_sequence":0})
request = read_message(sys.stdin.buffer)
write_message(sys.stdout.buffer, {"ok":True,**channel.handle(request)})
"""


@unittest.skipUnless(sys.platform == "linux" and os.environ.get("OMNINODE_BROWSER_INTEGRATION") == "1", "opt-in Linux Chromium native pipe fixture")
class NativeBrowserTest(unittest.IsolatedAsyncioTestCase):
    async def test_real_native_pipe_and_bounded_image(self):
        from playwright.async_api import async_playwright
        print("NATIVE_TEST_ENV", {"python":sys.version.split()[0], "playwright":importlib.metadata.version("playwright"), "Pillow":importlib.metadata.version("Pillow")}, flush=True)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            extension = root / "extension"
            extension.mkdir()
            profile = root / "profile"
            profile.mkdir()
            (extension / "manifest.json").write_text(json.dumps({"manifest_version":3,"name":"OmniNode isolated native wire test","version":"0.0.1","permissions":["nativeMessaging"],"background":{"service_worker":"worker.js"}}))
            (extension / "worker.js").write_text("chrome.runtime.onInstalled.addListener(() => {});")
            script = root / "fixture.py"
            script.write_text("import sys\nsys.path.insert(0," + repr(str(Path(__file__).resolve().parent)) + ")\n" + HOST_SCRIPT)
            stderr = root / "fixture.stderr"
            host = root / "fixture_host"
            libdir = sysconfig.get_config_var("LIBDIR") or str(Path(sys.prefix) / "lib")
            host.write_text("#!/bin/sh\nexport LD_LIBRARY_PATH=" + shlex.quote(libdir) + ':"${LD_LIBRARY_PATH:-}"\nexec ' + shlex.quote(sys.executable) + " " + shlex.quote(str(script)) + ' "$@" 2>' + shlex.quote(str(stderr)) + "\n")
            host.chmod(0o700)
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(str(profile),channel="chromium",headless=True,args=["--no-sandbox",f"--disable-extensions-except={extension}",f"--load-extension={extension}"])
                try:
                    worker = context.service_workers[0] if context.service_workers else await context.wait_for_event("serviceworker", timeout=10000)
                    extension_id = await worker.evaluate("chrome.runtime.id")
                    directory = profile / "NativeMessagingHosts"
                    directory.mkdir()
                    (directory / "com.omninode.desktop.json").write_text(json.dumps({"name":"com.omninode.desktop","description":"isolated fixture only","path":str(host),"type":"stdio","allowed_origins":["chrome-extension://" + extension_id + "/"]}))
                    result = await worker.evaluate("""() => new Promise((resolve,reject)=>{
                      const port=chrome.runtime.connectNative('com.omninode.desktop');let handshake=null;
                      const timer=setTimeout(()=>{port.disconnect();reject(Error('wire test timeout'))},15000);
                      port.onDisconnect.addListener(()=>{const e=chrome.runtime.lastError;if(e){clearTimeout(timer);reject(Error(e.message))}});
                      port.onMessage.addListener(message=>{
                        if(!message.ok){clearTimeout(timer);reject(Error(message.error || 'native fixture failure'));return}
                        if(!handshake){handshake=message;port.postMessage({session_id:message.session_id,sequence:0,action:'screenshot',args:{}})}
                        else{clearTimeout(timer);if(!message.result){reject(Error('native result absent'));return}resolve({handshake_ok:handshake.ok,result_mime:message.result.mime,source_width:message.result.width,preview_width:message.result.preview_width,base64_length:message.result.data_base64.length,session_correlated:message.session_id===handshake.session_id,sequence:message.sequence});port.disconnect()}
                      });
                      port.postMessage({type:'open',conversation:'fixture'});
                    })""")
                    self.assertTrue(result["handshake_ok"])
                    self.assertTrue(result["session_correlated"])
                    self.assertEqual(result["sequence"], 0)
                    self.assertEqual(result["result_mime"], "image/jpeg")
                    self.assertEqual(result["source_width"], 1600)
                    self.assertLessEqual(result["preview_width"], 1280)
                    self.assertLess(result["base64_length"], 1048576)
                except Exception:
                    if stderr.exists():
                        print("NATIVE_FIXTURE_STDERR", stderr.read_text(errors="replace")[-8000:], flush=True)
                    raise
                finally:
                    await context.close()


if __name__ == "__main__":
    unittest.main()
