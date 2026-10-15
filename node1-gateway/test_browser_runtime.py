import asyncio
import unittest
from browser_runtime import BiometricBrowserRuntime
from playwright.async_api import async_playwright

class TestBiometricBrowserIntegration(unittest.TestCase):
    def test_browser_initialization_and_patches(self):
        async def run():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Applica le patch anti-detection
                await BiometricBrowserRuntime.apply_stealth_patches(page)

                # Naviga su una pagina vuota per attivare il contesto ed eseguire lo script init
                await page.goto("about:blank")

                # Verifica che il flag navigator.webdriver sia undefined
                webdriver_val = await page.evaluate("navigator.webdriver")
                self.assertIsNone(webdriver_val)

                await browser.close()

        asyncio.run(run())

if __name__ == "__main__":
    unittest.main()
