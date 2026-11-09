"use strict";
const OmniActionPolicy=(()=>{
 const id=x=>typeof x==="string"&&/^[A-Za-z0-9._-]{8,128}$/.test(x);
 function validate(action,args){
  if(!args||Array.isArray(args)||typeof args!=="object")throw Error("INVALID_ACTION");
  if(action==="screenshot")return;
  if(["move","click","drag","notepad_write"].includes(action)){
   if(!Number.isSafeInteger(args.x)||!Number.isSafeInteger(args.y)||args.x<0||args.y<0)throw Error("INVALID_POINT");
  }
  if(["type","notepad_write"].includes(action)){
   if(typeof args.text!=="string"||args.text.length<1||args.text.length>256)throw Error("INVALID_TEXT");
  }
 }
 return {validate,id};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=OmniActionPolicy;else globalThis.OmniActionPolicy=OmniActionPolicy;