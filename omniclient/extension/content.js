(() => {
  const OMNICALL_PATTERN = /```omnicall\s*([\s\S]*?)```/g;
  const processed = new Set();
  let active = false;
  let observer = null;

  const button = document.createElement("button");
  button.textContent = "OmniNode OFF";
  button.style.cssText = `
    position: fixed;
    right: 18px;
    bottom: 18px;
    z-index: 2147483647;
    padding: 8px 12px;
    border: 0;
    border-radius: 999px;
    background: #1f2937;
    color: #fff;
    font: 600 13px system-ui, sans-serif;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(0,0,0,.25);
  `;

  button.addEventListener("click", () => {
    active = !active;
    button.textContent = active ? "OmniNode ON" : "OmniNode OFF";
    button.style.background = active ? "#059669" : "#1f2937";
    if (active) {
      scan();
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    } else if (observer) {
      observer.disconnect();
    }
  });

  function findComposer() {
    return document.querySelector(
      'rich-textarea div[contenteditable="true"], div[contenteditable="true"][role="textbox"]'
    );
  }

  async function execute(request) {
    const response = await chrome.runtime.sendMessage({
      type: "omninode-execute",
      request_id: request.request_id,
      path: request.path,
      content: request.content
    });

    const result = response?.ok
      ? `OmniNode: file creato\n${response.payload?.path ?? request.path}`
      : `OmniNode: operazione non completata\n${response?.error ?? response?.payload?.error ?? "errore sconosciuto"}`;

    insertResult(result);
  }

  function insertResult(text) {
    const composer = findComposer();
    if (composer && document.activeElement !== composer) {
      composer.focus();
      const block = `\n\n[OmniNode result]\n${text}\n[/OmniNode result]`;
      document.execCommand("insertText", false, block);
      composer.blur();
      return;
    }

    navigator.clipboard.writeText(`[OmniNode result]\n${text}\n[/OmniNode result]`);
  }

  function scan() {
    const text = document.body.innerText || "";
    for (const match of text.matchAll(OMNICALL_PATTERN)) {
      try {
        const request = JSON.parse(match[1].trim());
        if (!request.request_id || processed.has(request.request_id)) {
          continue;
        }
        processed.add(request.request_id);
        execute(request);
      } catch {
        // Ignora blocchi incompleti o JSON non valido: Gemini potrebbe essere ancora in streaming.
      }
    }
  }

  observer = new MutationObserver(() => {
    if (active) {
      scan();
    }
  });

  document.body.appendChild(button);
})();
