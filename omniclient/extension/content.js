(() => {
  "use strict";
  const REQUEST_ID = /^[A-Za-z0-9._-]{8,128}$/;

  function parseRequest(text) {
    const value = JSON.parse(text.trim());
    if (!value || Array.isArray(value) || typeof value !== "object") throw Error("Oggetto richiesto");
    if (Object.keys(value).sort().join(",") !== "action,args,request_id") throw Error("Schema non valido");
    if (typeof value.request_id !== "string" || !REQUEST_ID.test(value.request_id)) throw Error("ID non valido");
    if (value.action !== "screenshot") throw Error("Azione non autorizzata");
    if (!value.args || Array.isArray(value.args) || typeof value.args !== "object" || Object.keys(value.args).length) throw Error("Argomenti non validi");
    return value;
  }

  function canDeliver(active, sameConversation, streaming, text) {
    return Boolean(active && sameConversation && !streaming && String(text ?? "").trim() === "");
  }

  function isSettled(response, stableForMs) {
    const streaming = Boolean(response.closest('[aria-busy="true"], [data-is-streaming="true"]') || document.querySelector('button[data-test-id="stop-button"], button[aria-label="Stop response"], button[aria-label="Interrompi risposta"], button[aria-label="Stop generating"], button[aria-label="Interrompi generazione"]'));
    if (streaming) return false;
    const complete = response.getAttribute("aria-busy") === "false" || response.getAttribute("data-is-streaming") === "false";
    return complete && stableForMs >= 3000;
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {parseRequest, canDeliver, isSettled};
    return;
  }
  if (globalThis.__omninodeBridge) return;
  globalThis.__omninodeBridge = true;

  const SELECTORS = "model-response";
  let session = null;
  const snapshots = new WeakMap();
  const processed = new Set();

  const panel = document.createElement("div");
  panel.id = "omninode-bridge-results";
  panel.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:2147483647;background:#18212f;color:white;padding:12px;border-radius:10px;font:13px system-ui;max-width:360px;max-height:70vh;overflow:auto;display:none";
  document.body.append(panel);

  function status(text) {
    panel.style.display = "block";
    panel.textContent = text;
  }

  function stop(message) {
    session = null;
    processed.clear();
    status(message || "Sessione OmniNode terminata; nessuna nuova esecuzione");
  }

  function renderResult(message) {
    if (!session || message.request_id !== session.pendingRequestId) return;
    session.pendingRequestId = null;
    const card = document.createElement("div");
    card.style.cssText = "margin-top:10px;padding-top:10px;border-top:1px solid #3c4a5d";
    const title = document.createElement("strong");
    title.textContent = `Risultato ${message.request_id}`;
    card.append(title);
    const result = message.result;
    const image = result?.kind === "image" ? result : null;
    if (image && image.width <= 1280 && image.height <= 800 && image.bytes <= 614400 && typeof image.data_url === "string" && image.data_url.startsWith("data:image/")) {
      const img = document.createElement("img");
      img.src = image.data_url;
      img.alt = `Screenshot ${message.request_id}`;
      img.style.cssText = "display:block;max-width:100%;margin-top:8px;border-radius:6px";
      card.append(img);
    } else if (message.ok) {
      const pre = document.createElement("pre");
      pre.style.cssText = "white-space:pre-wrap;margin:8px 0 0";
      pre.textContent = JSON.stringify(result ?? {}, null, 2).slice(0, 4000);
      card.append(pre);
    } else {
      const error = document.createElement("div");
      error.style.cssText = "margin-top:8px;color:#fca5a5";
      error.textContent = message.error || "Operazione non completata";
      card.append(error);
    }
    panel.append(card);
  }

  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if (message?.type === "omninode-activation") {
      if (typeof message.activation_id !== "string" || message.activation_id.length < 32 || message.activation_id.length > 128) {
        reply({ok:false, error:"Invalid activation token"});
        return false;
      }
      if (typeof message.conversation !== "string" || message.conversation !== location.origin + location.pathname) {
        reply({ok:false, error:"Conversation binding mismatch"});
        return false;
      }
      if (!Number.isSafeInteger(message.expires_at) || message.expires_at <= Date.now()) {
        reply({ok:false, error:"Invalid activation expiry"});
        return false;
      }
      session = {token:message.activation_id, conversation:message.conversation, expiresAt:message.expires_at, started:Date.now(), baseline:new WeakSet(document.querySelectorAll(SELECTORS)), pendingRequestId:null};
      processed.clear();
      status("Sessione autorizzata: attendo una nuova risposta strutturata");
      reply({ok:true});
      return false;
    }
    if (message?.type === "ai-bridge-result") {
      renderResult(message);
      reply({ok:true});
      return false;
    }
    return false;
  });

  setInterval(() => {
    if (!session) return;
    if (location.origin + location.pathname !== session.conversation) { stop("Conversazione cambiata: sessione terminata"); return; }
    if (Date.now() > session.expiresAt) { stop("Sessione scaduta: nessuna nuova esecuzione"); return; }
    if (session.pendingRequestId) return;

    const responses = [...document.querySelectorAll(SELECTORS)];
    const response = responses.at(-1);
    if (!response || session.baseline.has(response)) return;
    const text = response.textContent || "";
    const snapshot = snapshots.get(response);
    if (!snapshot || snapshot.text !== text) {
      snapshots.set(response, {text, since:Date.now()});
      return;
    }
    const stableForMs = Date.now() - snapshot.since;
    if (!isSettled(response, stableForMs)) return;

    const blocks = [...response.querySelectorAll("pre code, pre")].filter(element => element.tagName === "CODE" || !element.querySelector("code"));
    if (blocks.length !== 1) { status("Attendo una nuova risposta con un solo blocco operativo"); return; }
    let request;
    try { request = parseRequest(blocks[0].textContent || ""); }
    catch (error) { status("Richiesta non riconosciuta: " + error.message); return; }
    if (processed.has(request.request_id)) { status("request_id già elaborato: nessuna riesecuzione"); return; }

    processed.add(request.request_id);
    session.pendingRequestId = request.request_id;
    status("Esecuzione richiesta: " + request.request_id);
    chrome.runtime.sendMessage({
      type:"ai-bridge-request",
      activation_id:session.token,
      request_id:request.request_id,
      issued_at:Date.now(),
      stream_state:"settled",
      payload:{action:request.action, args:request.args}
    }).then(responseMessage => {
      renderResult({request_id:request.request_id, ok:Boolean(responseMessage?.ok), result:responseMessage?.result, error:responseMessage?.error});
    }).catch(error => {
      renderResult({request_id:request.request_id, ok:false, error:String(error?.message || error)});
    });
  }, 500);
})();
