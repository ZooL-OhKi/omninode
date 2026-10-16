"use strict";
const statusNode=document.getElementById("status");
async function send(message) {
  try {
    const result=await chrome.runtime.sendMessage(message);
    if (!result?.ok) throw new Error(result?.error || "No service-worker response");
    statusNode.textContent=result.conversation ? "Sessione: " + result.conversation : "Operazione completata";
    return result;
  } catch(error) { statusNode.textContent=String(error.message || error); return null; }
}
document.getElementById("open").onclick=async()=>{
  const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
  statusNode.textContent="Attendo consenso nella finestra locale OmniNode";
  await send({type:"desktop-open",tabId:tab?.id});
};
document.getElementById("stop").onclick=async()=>{await send({type:"desktop-stop"});document.getElementById("preview").removeAttribute("src")};
document.getElementById("capture").onclick=async()=>{
  const result=await send({type:"desktop-execute",action:"screenshot",args:{}});
  const image=result?.result;
  if (image?.mime === "image/png" && typeof image.data_base64 === "string" && image.data_base64.length <= 1048576 && /^[A-Za-z0-9+/]*={0,2}$/.test(image.data_base64)) {
    document.getElementById("preview").src="data:image/png;base64," + image.data_base64;
  }
};
for (const button of document.querySelectorAll("[data-provider]")) button.onclick=()=>send({type:"ai-open",provider:button.dataset.provider});
send({type:"desktop-status"}).then(result=>{if(result && !result.active) statusNode.textContent="Desktop OFF: host locale da installare e consenso richiesto"});
