const BRIDGE_URL = "http://127.0.0.1:8080/api/bridge/execute";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "omninode-execute") {
    return false;
  }

  chrome.storage.local.get(["bridgeToken"], async (items) => {
    const token = items.bridgeToken;
    if (!token || token.length < 32) {
      sendResponse({ ok: false, error: "Token bridge non configurato" });
      return;
    }

    try {
      const response = await fetch(BRIDGE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          "Origin": "http://127.0.0.1:8080"
        },
        body: JSON.stringify({
          request_id: message.request_id,
          path: message.path,
          content: message.content
        })
      });

      const payload = await response.json();
      sendResponse({ ok: response.ok, status: response.status, payload });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
  });

  return true;
});
