"use strict";
importScripts("native_client.js", "desktop_broker.js");
const desktopBroker = new OmniDesktopBroker(chrome, new OmniNativeClient(chrome.runtime));
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
  if (message?.type === "omninode-execute") {
    reply({ok:false,error:"Legacy HTTP execution disabled pending session/origin hardening"});
    return false;
  }
  if (!message || !["desktop-open","desktop-stop","desktop-status","desktop-execute","ai-open","ai-focus"].includes(message.type)) return false;
  desktopBroker.handle(message,sender).then(reply).catch(error=>reply({ok:false,error:String(error.message || error)}));
  return true;
});
chrome.tabs.onRemoved.addListener(tabId=>{if(desktopBroker.owner?.tabId === tabId) desktopBroker.stop();desktopBroker.helpers.delete(tabId)});
chrome.tabs.onUpdated.addListener((tabId,change)=>{if(change.url) desktopBroker.changed(tabId,change.url)});
