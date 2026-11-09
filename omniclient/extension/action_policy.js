"use strict";
const OmniActionPolicy=(()=>{
 const id=x=>typeof x==="string"&&/^[A-Za-z0-9._-]{8,128}$/.test(x);
 const schemas={screenshot:[],move:["x","y"],click:["x","y","button"],drag:["x","y","to_x","to_y"],type:["text"],press:["key"],hotkey:["keys"],scroll:["steps"],notepad_write:["x","y","text","share_result"]};
 function validate(action,args){
  if(typeof action!=="string"||!Object.hasOwn(schemas,action)||!args||Array.isArray(args)||typeof args!=="object")throw Error("INVALID_ACTION");
  const fields=schemas[action];
  const metadata=action==="screenshot"?[]:["reference_id","observation_id","coord_space"];
  if(fields.some(k=>!Object.hasOwn(args,k))||Object.keys(args).some(k=>!fields.includes(k)&&!metadata.includes(k)))throw Error("INVALID_ACTION_SCHEMA");
  if(action==="screenshot")return;
  if(Object.hasOwn(args,"reference_id")&&!id(args.reference_id))throw Error("INVALID_REFERENCE");
  if(Object.hasOwn(args,"observation_id")||Object.hasOwn(args,"coord_space")){
   if(!id(args.observation_id)||args.coord_space!=="image_pixels")throw Error("INVALID_OBSERVATION_REFERENCE");
  }
  const point=(x,y)=>{if(!Number.isSafeInteger(x)||!Number.isSafeInteger(y)||x<0||y<0||x>=1280||y>=800)throw Error("INVALID_POINT");};
  if(["move","click","drag","notepad_write"].includes(action))point(args.x,args.y);
  if(action==="drag")point(args.to_x,args.to_y);
  if(action==="click"&&!["left","right","middle"].includes(args.button))throw Error("INVALID_BUTTON");
  if(["type","notepad_write"].includes(action)){
   if(typeof args.text!=="string"||args.text.length<1||args.text.length>256||/[\u0000-\u001f\u007f-\u009f\ud800-\udfff]/.test(args.text))throw Error("INVALID_TEXT");
  }
  const key=k=>typeof k==="string"&&/^[A-Za-z0-9_ -]{1,32}$/.test(k);
  if(action==="press"&&!key(args.key))throw Error("INVALID_KEY");
  if(action==="hotkey"&&(!Array.isArray(args.keys)||args.keys.length<1||args.keys.length>4||!args.keys.every(key)))throw Error("INVALID_KEYS");
  if(action==="scroll"&&(!Number.isSafeInteger(args.steps)||Math.abs(args.steps)>20))throw Error("INVALID_SCROLL");
  if(action==="notepad_write"&&(args.share_result!==true||!id(args.observation_id||args.reference_id)))throw Error("TASK_SHARING_REQUIRED");
 }
 return {validate,id};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=OmniActionPolicy;else globalThis.OmniActionPolicy=OmniActionPolicy;
