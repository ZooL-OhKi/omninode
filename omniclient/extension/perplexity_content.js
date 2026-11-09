(() => {
  "use strict";
  if (globalThis.__omniPerplexityAdapter) return;
  globalThis.__omniPerplexityAdapter = true;
  const MAX_WAIT_MS = 60000;
  const processed = new WeakSet();
  let activation = null;
  let expiresAt = 0;
  let conversation = null;
  let statusHost = null;
  let statusText = null;
  let observer = null;
  const currentConversation = () => location.origin + location.pathname;
  function show(text) {
    if (!statusHost) {
      statusHost = document.createElement("div");
      statusHost.style.cssText = "position:fixed;bottom:12px;right:12px;z-index:2147483647;max-width:340px";
      const shadow = statusHost.attachShadow({ mode: "closed" });
      statusText = document.createElement("div");
      statusText.style.cssText = "background:#18212f;color:white;padding:10px;border-radius:8px;font:12px system-ui";
      shadow.append(statusText);
      document.documentElement.append(statusHost);
    }
    statusText.textContent = text;
  }
  function markHistorical() {
    document.querySelectorAll(".group\\/final-text").forEach((partition) => processed.add(partition));
  }
  function waitForCompletion(partition) {
    return new Promise((resolve) => {
      const started = Date.now();
      const timer = setInterval(() => {
        if (Date.now() - started > MAX_WAIT_MS) {
          clearInterval(timer);
          resolve(false);
          return;
        }
        if (omniIsCompleted(partition)) {
          clearInterval(timer);
          resolve(true);
        }
      }, 500);
    });
  }
  async function deliverResult(text) {
    const composers = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]')).filter((el) => el.offsetParent !== null);
    const composer = composers[composers.length - 1];
    if (!composer) return false;
    if ((composer.textContent || "").trim()) return false;
    composer.focus();
    const inserted = document.execCommand("insertText", false, text);
    if (!inserted) return false;
    const send = Array.from(document.querySelectorAll('button[aria-label="Invia"]')).find((button) => !button.disabled);
    if (!send) return false;
    send.click();
    return true;
  }
  async function processPartition(partition) {
    if (processed.has(partition)) return;
    processed.add(partition);
    const completed = await waitForCompletion(partition);
    if (!completed) {
      show("OmniNode: risposta non completata entro il limite.");
      return;
    }
    const text = omniExtractResponseText(partition);
    const command = omniParseCommand(text, globalThis.OmniActionPolicy);
    if (!command) return;
    let response;
    try {
      response = await chrome.runtime.sendMessage({
        type: "ai-bridge-request",
        request_id: command.request_id,
        issued_at: Date.now(),
        stream_state: "settled",
        payload: { action: command.action, args: command.args }
      });
    } catch {
      show("OmniNode: invio comando non riuscito.");
      return;
    }
    if (!response || response.ok !== true || response.request_id !== command.request_id) {
      show("OmniNode: esito comando non certo; nessun retry.");
      return;
    }
    const delivered = await deliverResult(omniBuildResultMessage(command, response));
    show(delivered ? "OmniNode: risultato inviato alla chat." : "OmniNode: risultato acquisito ma invio alla chat non riuscito.");
  }
  function startObserver() {
    if (observer) return;
    observer = new MutationObserver(() => {
      document.querySelectorAll(".group\\/final-text").forEach((partition) => {
        if (!processed.has(partition)) processPartition(partition);
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if (message?.type !== "omninode-activation") return false;
    if (sender.id !== chrome.runtime.id || !/^[a-f0-9]{64}$/.test(message.activation_id || "") || !Number.isSafeInteger(message.expires_at) || message.expires_at <= Date.now() || message.conversation !== currentConversation()) {
      reply({ ok: false });
      return false;
    }
    const candidate = message.activation_id;
    activation = candidate;
    expiresAt = message.expires_at;
    conversation = message.conversation;
    chrome.runtime.sendMessage({ type: "bridge-bind", activation_id: candidate }).then((result) => {
      if (activation !== candidate || Date.now() >= expiresAt || conversation !== currentConversation() || result?.ok !== true || result.activation_id !== candidate) {
        if (activation === candidate) activation = null;
        reply({ ok: false });
        return;
      }
      markHistorical();
      startObserver();
      show("OmniNode: pagina collegata. Comandi screenshot dalle nuove risposte attivi.");
      reply({ ok: true });
    }).catch(() => {
      if (activation === candidate) activation = null;
      show("OmniNode: collegamento pagina non riuscito.");
      reply({ ok: false });
    });
    return true;
  });
  setInterval(() => {
    if (!activation) return;
    if (Date.now() >= expiresAt || currentConversation() !== conversation) {
      activation = null;
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      show("OmniNode: sessione scaduta o conversazione cambiata. Riattiva dal popup.");
      chrome.runtime.sendMessage({ type: "desktop-stop" }).catch(() => {});
    }
  }, 1000);
})();
