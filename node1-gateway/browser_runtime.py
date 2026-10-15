import asyncio
import math
import random

class BiometricBrowserRuntime:
    """Runtime di navigazione isolato con patch anti-detection e biometria umana."""

    @staticmethod
    async def apply_stealth_patches(page):
        """Applica le patch critiche per aggirare i controlli anti-bot moderni."""
        await page.add_init_script("""
            // 1. Rimuove il flag navigator.webdriver (restituisce undefined)
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 2. Patch delle permessioni
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );

            // 3. Normalizzazione WebGL Vendor/Renderer per coerenza hardware
            try {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter.apply(this, arguments);
                };
            } catch (e) {}

            // 4. Isolamento contentWindow degli iframe
            const origCreateElement = document.createElement.bind(document);
            document.createElement = function(...args) {
                const element = origCreateElement(...args);
                if (args[0] && args[0].toLowerCase() === 'iframe') {
                    Object.defineProperty(element, 'contentWindow', {
                        get: function() {
                            const win = this.contentWindow;
                            if (win) {
                                Object.defineProperty(win.navigator, 'webdriver', { get: () => undefined });
                            }
                            return win;
                        }
                    });
                }
                return element;
            };
        """)

    @staticmethod
    async def human_type(page, selector: str, text: str):
        """Digita il testo simulando la cadenza biologica umana con distribuzioni gaussiane."""
        element = page.locator(selector)
        await element.click()

        for char in text:
            delay = max(0.04, random.gauss(0.09, 0.03))
            await asyncio.sleep(delay)

            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 0.7))

            await page.keyboard.type(char)

    @staticmethod
    async def human_move_and_click(page, selector: str):
        """Simula lo spostamento del mouse tramite curve di Bézier e clicca sull'elemento."""
        target = page.locator(selector)
        box = await target.bounding_box()
        if not box:
            await target.click()
            return

        dest_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        dest_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

        curr = await page.evaluate("() => ({ x: window.lastMouseX || 100, y: window.lastMouseY || 100 })")
        start_x, start_y = curr["x"], curr["y"]

        ctrl1_x = start_x + (dest_x - start_x) * random.uniform(0.2, 0.4) + random.randint(-30, 30)
        ctrl1_y = start_y + (dest_y - start_y) * random.uniform(0.1, 0.5) + random.randint(-30, 30)
        ctrl2_x = start_x + (dest_x - start_x) * random.uniform(0.6, 0.8) + random.randint(-30, 30)
        ctrl2_y = start_y + (dest_y - start_y) * random.uniform(0.5, 0.9) + random.randint(-30, 30)

        steps = random.randint(25, 45)
        for i in range(steps + 1):
            t = i / float(steps)
            xt = (1-t)**3 * start_x + 3*(1-t)**2 * t * ctrl1_x + 3*(1-t)*t**2 * ctrl2_x + t**3 * dest_x
            yt = (1-t)**3 * start_y + 3*(1-t)**2 * t * ctrl1_y + 3*(1-t)*t**2 * ctrl2_y + t**3 * dest_y

            await page.mouse.move(xt, yt)
            await asyncio.sleep(random.uniform(0.005, 0.015))

        await page.evaluate(f"window.lastMouseX = {dest_x}; window.lastMouseY = {dest_y};")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await page.mouse.click(dest_x, dest_y)
