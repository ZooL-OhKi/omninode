"use strict";
const moveDeps=typeof module!=="undefined"&&module.exports?{...require("./desktop_broker.js"),...require("./bridge_result.js")}:globalThis;
class OmniMoveBroker extends moveDeps.OmniDesktopBroker {
 recordObservation(s,id,image){if(!this.isCurrent(s))return;moveDeps.mapScreenshotPoint(image,0,0);s.observation={id,image,at:Date.now()};}
 async bridge(m,sender){
  if(m?.type!=="ai-bridge-request"||m?.payload?.action!=="move")return super.bridge(m,sender);
  const s=this._assertActiveBridge(sender,m);
  const reject=code=>{throw new moveDeps.BridgeRejectedError(code);};
  if(typeof m.request_id!=="string"||!/^[A-Za-z0-9._-]{8,128}$/.test(m.request_id))reject("INVALID_REQUEST_ID");
  if(s.requests.has(m.request_id))reject("DUPLICATE_REQUEST");
  if(s.requests.size>=this.maxRequests)reject("REQUEST_LIMIT");
  if(!Number.isSafeInteger(m.issued_at)||m.issued_at<s.issuedAt||m.issued_at>Date.now()+5000)reject("INVALID_TIMESTAMP");
  const p=m.payload,a=p.args;
  if(Object.keys(p).sort().join(",")!=="action,args"||!a||Array.isArray(a)||typeof a!=="object"||Object.keys(a).sort().join(",")!=="reference_id,x,y"||typeof a.reference_id!=="string"||!/^[A-Za-z0-9._-]{8,128}$/.test(a.reference_id))reject("INVALID_PAYLOAD");
  const observation=s.observation;
  if(!observation||observation.id!==a.reference_id||Date.now()<observation.at||Date.now()-observation.at>60000)reject("STALE_SCREEN_REFERENCE");
  let point;try{point=moveDeps.mapScreenshotPoint(observation.image,a.x,a.y);}catch{reject("INVALID_PREVIEW_POINT");}
  s.inFlightRequestId=m.request_id;s.requests.set(m.request_id,{status:"pending"});s.observation=null;
  try{
   const tab=await this.api.tabs.get(s.tabId);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(moveDeps.omniConversation(tab.url)!==s.conversation){this.stop();return {stale_dropped:true};}
   if(!tab.active)throw new moveDeps.BridgeRejectedError("TAB_NOT_ACTIVE");
   if(Date.now()-observation.at>60000)throw new moveDeps.BridgeRejectedError("STALE_SCREEN_REFERENCE");
   const ack=await this.client.execute("move",point);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(ack?.ok!==true||ack.result?.status!=="executed"||ack.result?.action!=="move")throw Error("INVALID_MOVE_RESULT");
   const result=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   s.requests.set(m.request_id,{status:"completed"});
   return {ok:true,request_id:m.request_id,activation_id:s.activationId,result,_session:s,completed_action:"move",action_result:{status:"executed",preview:{x:a.x,y:a.y},native:point,reference_id:a.reference_id}};
  }catch(error){
   if(this.session!==s||this.epoch!==s.epoch||Date.now()>=s.expiresAt){if(this.session===s)this.stop();return {stale_dropped:true};}
   this.stop();if(error.rejected)throw error;throw new moveDeps.BridgeFatalError("MOVE_OR_OBSERVATION_UNCERTAIN_NO_RETRY");
  }finally{if(this.session===s)s.inFlightRequestId=null;}
 }
}
if(typeof module!=="undefined"&&module.exports)module.exports={OmniMoveBroker};else globalThis.OmniMoveBroker=OmniMoveBroker;
