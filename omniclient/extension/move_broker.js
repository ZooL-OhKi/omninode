"use strict";
const moveDeps=typeof module!=="undefined"&&module.exports?{...require("./desktop_broker.js"),...require("./bridge_result.js"),OmniActionPolicy:require("./action_policy.js")}:globalThis;
class OmniMoveBroker extends moveDeps.OmniDesktopBroker {
 recordObservation(s,id,image){if(!this.isCurrent(s))return;moveDeps.mapScreenshotPoint(image,0,0);s.observation={id,image,at:Date.now()};}
 async bridge(m,sender){
  if(m?.type!=="ai-bridge-request"||m?.payload?.action==="screenshot")return super.bridge(m,sender);
  const s=this._assertActiveBridge(sender,m),reject=code=>{throw new moveDeps.BridgeRejectedError(code);};
  if(!moveDeps.OmniActionPolicy.id(m.request_id))reject("INVALID_REQUEST_ID");
  if(s.requests.has(m.request_id))reject("DUPLICATE_REQUEST");
  const p=m.payload;
  if(!p||Array.isArray(p)||!p.action||!p.args)reject("INVALID_PAYLOAD");
  try{moveDeps.OmniActionPolicy.validate(p.action,p.args);}catch{reject("INVALID_PAYLOAD");}
  const a=p.args;
  s.inFlightRequestId=m.request_id;s.requests.set(m.request_id,{status:"pending"});
  try{
   const before=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   const obsImage=moveDeps.normalizeBridgeScreenshot(before);
   const args={x:a.x,y:a.y,text:a.text,button:a.button,to_x:a.to_x,to_y:a.to_y,steps:a.steps,key:a.key,keys:a.keys};
   Object.keys(args).forEach(k=>args[k]===undefined&&delete args[k]);
   if(["move","click","drag","notepad_write"].includes(p.action)&& obsImage.width && obsImage.source_width){
    if(a.x<=obsImage.width && a.y<=obsImage.height){
     try{Object.assign(args,moveDeps.mapScreenshotPoint(obsImage,a.x,a.y));}catch{}
    }
   }
   const ack=await this.client.execute(p.action,args);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(ack?.ok!==true||ack.result?.status!=="executed")throw Error("INVALID_ACTION_RESULT");
   const result=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   s.requests.set(m.request_id,{status:"completed"});
   return {ok:true,request_id:m.request_id,activation_id:s.activationId,result,_session:s,completed_action:p.action,auto_delivery:true,action_result:{status:"executed",reference_id:a.reference_id||m.request_id}};
  }catch(error){this.stop();if(error.rejected)throw error;throw new moveDeps.BridgeFatalError("ACTION_OR_OBSERVATION_UNCERTAIN_NO_RETRY");}
  finally{if(this.session===s)s.inFlightRequestId=null;}
 }
}
if(typeof module!=="undefined"&&module.exports)module.exports={OmniMoveBroker};else globalThis.OmniMoveBroker=OmniMoveBroker;