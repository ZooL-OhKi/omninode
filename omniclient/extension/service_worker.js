"use strict";
function createBridgeListener(broker,normalize){
 return (message,sender,reply)=>{
  if(message?.type==="omninode-execute"){reply({ok:false,rejected:true,code:"LEGACY_DISABLED"});return false;}
  if(!["bridge-bind","ai-bridge-request","desktop-open","desktop-stop","desktop-status","desktop-execute","ai-open","ai-focus"].includes(message?.type))return false;
  broker.handle(message,sender).then(value=>{
   if(value?.stale_dropped){reply();return;}
   if(message.type!=="ai-bridge-request"){reply(value);return;}
   if(!broker.isCurrent(value._session)){reply();return;}
   let result;
   try{result=normalize(value.result);broker.recordObservation?.(value._session,value.request_id,result);}catch{if(broker.isCurrent(value._session))broker.stop();reply({ok:false,fatal:true,code:"INVALID_NATIVE_IMAGE",request_id:message.request_id,activation_id:value.activation_id});return;}
   if(!broker.isCurrent(value._session)){reply();return;}
   reply({ok:true,request_id:value.request_id,activation_id:value.activation_id,result,...(value.completed_action?{completed_action:value.completed_action,action_result:value.action_result}:{})});
  }).catch(error=>reply({ok:false,...(error.rejected?{rejected:true}:{fatal:true}),code:error.code||"INTERNAL_ERROR",...(message.type==="ai-bridge-request"?{request_id:message.request_id,activation_id:message.activation_id}:{})}));
  return true;
 };
}
if(typeof module!=="undefined"&&module.exports)module.exports={createBridgeListener};
else{
 importScripts("native_client.js","desktop_broker.js","bridge_result.js","action_policy.js","move_broker.js");
 const broker=new OmniMoveBroker(chrome,new OmniNativeClient(chrome.runtime));
 chrome.runtime.onMessage.addListener(createBridgeListener(broker,normalizeBridgeScreenshot));
 chrome.tabs.onRemoved.addListener(id=>{if(broker.owner?.tabId===id)broker.stop();broker.helpers.delete(id);});
 chrome.tabs.onUpdated.addListener((id,c)=>{if(c.status==="loading"&&broker.owner?.tabId===id)broker.stop();else if(c.url)broker.changed(id,c.url);});
}
