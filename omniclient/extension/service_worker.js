"use strict";
importScripts("native_client.js", "desktop_broker.js", "bridge_result.js");
const desktopBroker = new OmniDesktopBroker(chrome, new OmniNativeClient(chrome.runtime));
const MESSAGE_TYPES = ["desktop-open","desktop-stop","desktop-status","desktop-execute","ai-open","ai-focus","ai-bridge-request"];
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (message?.type === "omninode-execute") {
    reply({ok:false, error:"Legacy HTTP execution disabled pending session/origin hardening"});
    return false;
  }
  if (!message || !MESSAGE_TYPES.includes(message.type)) return false;
  const epoch = desktopBroker.epoch;
  desktopBroker.handle(message, sender).then(result => {
    if (message.type !== "ai-bridge-request") { reply(result); return; }
    if (desktopBroker.epoch !== epoch || !desktopBroker.owner || !desktopBroker.client.session || Date.now() > desktopBroker.activation?.expiresAt) throw Error("Bridge session revoked before result delivery");
    reply({ok:true, request_id:message.request_id, result:normalizeBridgeScreenshot(result.result)});
  }).catch(error => {
    if (message.type === "ai-bridge-request" && desktopBroker.epoch === epoch) desktopBroker.stop();
    reply({ok:false, ...(message.type === "ai-bridge-request" ? {request_id:message.request_id} : {}), error:String(error.message || error)});
  });
  return true;
});
chrome.tabs.onRemoved.addListener(tabId => {
  if (desktopBroker.owner?.tabId === tabId) desktopBroker.stop();
  desktopBroker.helpers.delete(tabId);
});
chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (change.url) desktopBroker.changed(tabId, change.url);
});
