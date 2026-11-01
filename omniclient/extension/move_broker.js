"use strict";
const moveDeps=typeof module!=="undefined"&&module.exports?{...require("./desktop_broker.js"),...require("./bridge_result.js"),OmniActionPolicy:require("./action_policy.js")}:globalThis;
class OmniMoveBroker extends moveDeps.OmniDesktopBroker {
 recordObservation(s,id,image){if(!this.isCurrent(s))return;moveDeps.mapScreenshotPoint(image,0,0);s.observation={id,image,at:Date.now()};}
 async bridge(m,sender){
  if(m?.type!=="ai-bridge-request"||m?.payload?.action==="screenshot")return super.bridge(m,sender);
  const s=this._assertActiveBridge(sender,m),reject=code=>{throw new moveDeps.BridgeRejectedError(code);};
  if(!moveDeps.OmniActionPolicy.id(m.request_id))reject("INVALID_REQUEST_ID");
  if(s.requests.has(m.request_id))reject("DUPLICATE_REQUEST");
  if(s.requests.size>=this.maxRequests)reject("REQUEST_LIMIT");
  if(!Number.isSafeInteger(m.issued_at)||m.issued_at<s.issuedAt||m.issued_at>Date.now()+5000)reject("INVALID_TIMESTAMP");
  const p=m.payload;
  if(!p||Array.isArray(p)||Object.keys(p).sort().join(",")!=="action,args")reject("INVALID_PAYLOAD");
  try{moveDeps.OmniActionPolicy.validate(p.action,p.args);}catch{reject("INVALID_PAYLOAD");}
  const a=p.args,o=s.observation;
  if(!o||o.id!==a.reference_id||Date.now()<o.at||Date.now()-o.at>60000)reject("STALE_SCREEN_REFERENCE");
  const args={...a};delete args.reference_id;
  if(p.action==="notepad_write")delete args.share_result;
  try{if(["move","click","drag","notepad_write"].includes(p.action))Object.assign(args,moveDeps.mapScreenshotPoint(o.image,a.x,a.y));if(p.action==="drag"){const end=moveDeps.mapScreenshotPoint(o.image,a.to_x,a.to_y);args.to_x=end.x;args.to_y=end.y;}}catch{reject("INVALID_PREVIEW_POINT");}
  s.inFlightRequestId=m.request_id;s.requests.set(m.request_id,{status:"pending"});s.observation=null;
  try{
   const tab=await this.api.tabs.get(s.tabId);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(moveDeps.omniConversation(tab.url)!==s.conversation){this.stop();return {stale_dropped:true};}
   if(!tab.active)throw new moveDeps.BridgeRejectedError("TAB_NOT_ACTIVE");
   const before=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   const geometry=moveDeps.normalizeBridgeScreenshot(before);
   if(geometry.source_width!==o.image.source_width||geometry.source_height!==o.image.source_height)throw new moveDeps.BridgeRejectedError("SCREEN_GEOMETRY_CHANGED");
   if(Date.now()<o.at||Date.now()-o.at>60000)throw new moveDeps.BridgeRejectedError("STALE_SCREEN_REFERENCE");
   const ack=await this.client.execute(p.action,args);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(ack?.ok!==true||ack.result?.status!=="executed"||ack.result?.action!==p.action)throw Error("INVALID_ACTION_RESULT");
   const result=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   s.requests.set(m.request_id,{status:"completed"});
   return {ok:true,request_id:m.request_id,activation_id:s.activationId,result,_session:s,completed_action:p.action,auto_delivery:p.action==="notepad_write"&&a.share_result===true,action_result:{status:"executed",reference_id:a.reference_id}};
  }catch(error){if(this.session!==s||this.epoch!==s.epoch||Date.now()>=s.expiresAt){if(this.session===s)this.stop();return {stale_dropped:true};}this.stop();if(error.rejected)throw error;throw new moveDeps.BridgeFatalError("ACTION_OR_OBSERVATION_UNCERTAIN_NO_RETRY");}
  finally{if(this.session===s)s.inFlightRequestId=null;}
 }
}
if(typeof module!=="undefined"&&module.exports)module.exports={OmniMoveBroker};else globalThis.OmniMoveBroker=OmniMoveBroker;
