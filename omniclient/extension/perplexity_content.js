(() => {
  "use strict";
  if (globalThis.__omniPerplexityHandshake) return;
  globalThis.__omniPerplexityHandshake = true;
  let activation = null;
  let expiresAt = 0;
  let conversation = null;
  let statusHost = null;
  let statusText = null;
  const currentConversation = () => location.origin + location.pathname;
  function show(text) {
    if (!statusHost) {
      statusHost = document.createElement("div");
      statusHost.style.cssText = "position:fixed;bottom:12px;right:12px;z-index:2147483647;max-width:340px";
      const shadow = statusHost.attachShadow({mode: "closed"});
      statusText = document.createElement("div");
      statusText.style.cssText = "background:#18212f;color:white;padding:10px;border-radius:8px;font:12px system-ui";
      shadow.append(statusText);
      document.documentElement.append(statusHost);
    }
    statusText.textContent = text;
  }
  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if (message?.type !== "omninode-activation") return false;
    if (sender.id !== chrome.runtime.id || !/^[a-f0-9]{64}$/.test(message.activation_id || "") || !Number.isSafeInteger(message.expires_at) || message.expires_at <= Date.now() || message.conversation !== currentConversation()) {
      reply({ok: false});
      return false;
    }
    const candidate = message.activation_id;
    activation = candidate;
    expiresAt = message.expires_at;
    conversation = message.conversation;
    chrome.runtime.sendMessage({type: "bridge-bind", activation_id: candidate}).then(result => {
      if (activation !== candidate || Date.now() >= expiresAt || conversation !== currentConversation() || result?.ok !== true || result.activation_id !== candidate) {
        if (activation === candidate) activation = null;
        reply({ok: false});
        return;
      }
      show("OmniNode: pagina collegata. Prova screenshot dal popup disponibile; lettura comandi e ritorno automatico alla chat non ancora implementati.");
      reply({ok: true});
    }).catch(() => {
      if (activation === candidate) activation = null;
      show("OmniNode: collegamento pagina non riuscito.");
      reply({ok: false});
    });
    return true;
  });
  setInterval(() => {
    if (!activation) return;
    if (Date.now() >= expiresAt || currentConversation() !== conversation) {
      activation = null;
      show("OmniNode: sessione scaduta o conversazione cambiata. Riattiva dal popup.");
      chrome.runtime.sendMessage({type: "desktop-stop"}).catch(() => {});
    }
  }, 1000);
})();
