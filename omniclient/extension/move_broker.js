"use strict";
const moveDeps=typeof module!=="undefined"&&module.exports?{...require("./desktop_broker.js"),...require("./bridge_result.js"),OmniActionPolicy:require("./action_policy.js")}:globalThis;
const OBSERVATION_TTL_MS=60000;
const MOVE_SCHEMAS={move:["x","y"],click:["x","y","button"],drag:["x","y","to_x","to_y"],notepad_write:["x","y","text"],type:["text"],press:["key"],hotkey:["keys"],scroll:["steps"]};
function validateMovePayload(action,args){
 if(!Object.hasOwn(MOVE_SCHEMAS,action)||!args||Array.isArray(args)||typeof args!=="object")throw Error("INVALID_ACTION");
 const keys=Object.keys(args).filter(k=>!["observation_id","coord_space","reference_id"].includes(k)).sort().join(",");
 if(keys!==[...MOVE_SCHEMAS[action]].sort().join(","))throw Error("INVALID_ACTION_SCHEMA");
 moveDeps.OmniActionPolicy.validate(action,args);
 if(action==="click"&&!["left","right","middle"].includes(args.button))throw Error("INVALID_BUTTON");
 if(action==="drag"&&(!Number.isSafeInteger(args.to_x)||!Number.isSafeInteger(args.to_y)||args.to_x<0||args.to_y<0))throw Error("INVALID_POINT");
 if(action==="scroll"&&(!Number.isSafeInteger(args.steps)||Math.abs(args.steps)>20))throw Error("INVALID_SCROLL");
 if(action==="press"&&(typeof args.key!=="string"||!args.key.length||args.key.length>32))throw Error("INVALID_KEY");
 if(action==="hotkey"&&(!Array.isArray(args.keys)||args.keys.length<1||args.keys.length>4||args.keys.some(k=>typeof k!=="string"||!k.length||k.length>32)))throw Error("INVALID_KEYS");
}
function requireObservation(s,args,now=Date.now()){
 const o=s.observation;
 if(!o||args.observation_id!==o.id)throw new moveDeps.BridgeRejectedError("OBSERVATION_REFERENCE_REQUIRED");
 if(!Number.isSafeInteger(o.at)||now<o.at||now-o.at>=OBSERVATION_TTL_MS)throw new moveDeps.BridgeRejectedError("STALE_OBSERVATION_REJECTED");
 if(args.coord_space!=="image_pixels")throw new moveDeps.BridgeRejectedError("INVALID_COORD_SPACE");
 return o;
}
class OmniMoveBroker extends moveDeps.OmniDesktopBroker {
 recordObservation(s,id,image){
  if(!this.isCurrent(s))return;
  moveDeps.mapScreenshotPoint(image,0,0);
  const at=Date.now();
  image.observation_id=id;image.observed_at_ms=at;image.observation_ttl_ms=OBSERVATION_TTL_MS;image.coord_space="image_pixels";
  s.observation={id,image:{...image},at};
 }
 async bridge(m,sender){
  if(m?.type!=="ai-bridge-request"||m?.payload?.action==="screenshot")return super.bridge(m,sender);
  const s=this._assertActiveBridge(sender,m),reject=code=>{throw new moveDeps.BridgeRejectedError(code);};
  if(!moveDeps.OmniActionPolicy.id(m.request_id))reject("INVALID_REQUEST_ID");
  if(s.requests.has(m.request_id))reject("DUPLICATE_REQUEST");
  if(s.requests.size>=this.maxRequests)reject("REQUEST_LIMIT");
  if(!Number.isSafeInteger(m.issued_at)||m.issued_at<s.issuedAt||m.issued_at>Date.now()+5000)reject("INVALID_TIMESTAMP");
  const p=m.payload;
  if(!p||Array.isArray(p)||Object.keys(p).sort().join(",")!=="action,args")reject("INVALID_PAYLOAD");
  try{validateMovePayload(p.action,p.args);}catch{reject("INVALID_PAYLOAD");}
  const a=p.args;
  const bound=/^https:\/\/(www\.)?perplexity\.ai\//.test(s.conversation)||Object.hasOwn(a,"observation_id");
  const reference=bound?requireObservation(s,a):null;
  if(reference){
   try{
    if(["move","click","drag","notepad_write"].includes(p.action))moveDeps.mapScreenshotPoint(reference.image,a.x,a.y);
    if(p.action==="drag")moveDeps.mapScreenshotPoint(reference.image,a.to_x,a.to_y);
   }catch{reject("POINT_OUTSIDE_PREVIEW");}
  }
  s.inFlightRequestId=m.request_id;s.requests.set(m.request_id,{status:"pending"});
  try{
   const before=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   const obsImage=moveDeps.normalizeBridgeScreenshot(before);
   if(reference){
    if(requireObservation(s,a)!==reference)reject("STALE_OBSERVATION_REJECTED");
    if(["width","height","source_width","source_height"].some(k=>obsImage[k]!==reference.image[k]))reject("OBSERVATION_GEOMETRY_CHANGED");
   }
   const args={x:a.x,y:a.y,text:a.text,button:a.button,to_x:a.to_x,to_y:a.to_y,steps:a.steps,key:a.key,keys:a.keys};
   Object.keys(args).forEach(k=>args[k]===undefined&&delete args[k]);
   const geometry=reference?reference.image:obsImage;
   if(["move","click","drag","notepad_write"].includes(p.action))Object.assign(args,moveDeps.mapScreenshotPoint(geometry,a.x,a.y));
   if(p.action==="drag"){
    const end=moveDeps.mapScreenshotPoint(geometry,a.to_x,a.to_y);args.to_x=end.x;args.to_y=end.y;
   }
   const ack=await this.client.execute(p.action,args);
   if(!this.isCurrent(s))return {stale_dropped:true};
   if(ack?.ok!==true||ack.result?.status!=="executed")throw Error("INVALID_ACTION_RESULT");
   const result=await this.client.execute("screenshot",{});
   if(!this.isCurrent(s))return {stale_dropped:true};
   s.requests.set(m.request_id,{status:"completed"});
   return {ok:true,request_id:m.request_id,activation_id:s.activationId,result,_session:s,completed_action:p.action,auto_delivery:true,action_result:{status:"executed",reference_id:reference?reference.id:(a.reference_id||m.request_id)}};
  }catch(error){this.stop();if(error.rejected)throw error;throw new moveDeps.BridgeFatalError("ACTION_OR_OBSERVATION_UNCERTAIN_NO_RETRY");}
  finally{if(this.session===s)s.inFlightRequestId=null;}
 }
}
if(typeof module!=="undefined"&&module.exports)module.exports={OmniMoveBroker,requireObservation,validateMovePayload,OBSERVATION_TTL_MS};else globalThis.OmniMoveBroker=OmniMoveBroker;
