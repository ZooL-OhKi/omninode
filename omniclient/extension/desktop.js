"use strict";
const statusNode = document.getElementById("status");
let statusVersion = 0;
async function send(message) {
  const version = ++statusVersion;
  try {
    const result = await chrome.runtime.sendMessage(message);
    if (!result?.ok) throw new Error(result?.code || result?.error || "EMPTY_SERVICE_WORKER_RESPONSE");
    if (version === statusVersion) {
      if (message.type === "desktop-status") {
        statusNode.textContent = result.active ? "Desktop attivo: " + (result.conversation || "sessione locale") : "Desktop inattivo. Premi Abilita sulla scheda selezionata per verificare il collegamento; host non ancora verificato dal browser.";
      } else if (message.type === "desktop-stop") {
        statusNode.textContent = "Desktop arrestato.";
      } else {
        statusNode.textContent = result.conversation ? "Sessione: " + result.conversation : "Operazione completata";
      }
    }
    return result;
  } catch (error) {
    if (version === statusVersion) statusNode.textContent = "Errore: " + String(error.message || error);
    return null;
  }
}
document.getElementById("open").onclick = async () => {
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    statusNode.textContent = "Connessione al canale nativo in corso...";
    await send({type: "desktop-open", tabId: tab?.id});
  } catch (error) {
    statusNode.textContent = "Errore: " + String(error.message || error);
  }
};
document.getElementById("stop").onclick = async () => {
  await send({type: "desktop-stop"});
  document.getElementById("preview").removeAttribute("src");
};
document.getElementById("capture").onclick = async () => {
  const preview = document.getElementById("preview");
  preview.removeAttribute("src");
  const result = await send({type: "desktop-execute", action: "screenshot", args: {}});
  if (!result) return;
  const image = result.result;
  if (!["image/png", "image/jpeg"].includes(image?.mime) || typeof image.data_base64 !== "string" || !image.data_base64.length || image.data_base64.length > 1048576 || !/^[A-Za-z0-9+/]*={0,2}$/.test(image.data_base64)) {
    statusNode.textContent = "Errore: risposta screenshot assente, non valida o oltre il limite.";
    return;
  }
  preview.onload = () => { statusNode.textContent = "Screenshot locale ricevuto. Invio alla chat non verificato."; };
  preview.onerror = () => { preview.removeAttribute("src"); statusNode.textContent = "Errore: immagine screenshot non decodificabile."; };
  preview.src = "data:" + image.mime + ";base64," + image.data_base64;
};
for (const button of document.querySelectorAll("[data-provider]")) {
  button.onclick = () => send({type: "ai-open", provider: button.dataset.provider});
}
send({type: "desktop-status"});
