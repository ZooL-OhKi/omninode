"use strict";
const OmniActionPolicy=(()=>{
 const schemas={screenshot:[],move:["reference_id","x","y"],click:["button","reference_id","x","y"],drag:["reference_id","to_x","to_y","x","y"],scroll:["reference_id","steps"],press:["key","reference_id"],hotkey:["keys","reference_id"],type:["reference_id","text"]};
 const id=x=>typeof x==="string"&&/^[A-Za-z0-9._-]{8,128}$/.test(x);
 const key=x=>typeof x==="string"&&(/^[a-z0-9]$/.test(x)||/^f(?:[1-9]|1[0-2])$/.test(x)||["ctrl","alt","shift","win","enter","esc","tab","backspace","delete","home","end","left","right","up","down","pageup","pagedown","space","capslock"].includes(x));
 function validate(action,args){
  if(!Object.hasOwn(schemas,action)||!args||Array.isArray(args)||typeof args!=="object"||Object.keys(args).sort().join(",")!==schemas[action].join(","))throw Error("INVALID_ACTION");
  if(action==="screenshot")return;
  if(!id(args.reference_id))throw Error("INVALID_REFERENCE");
  const point=(x,y)=>{if(!Number.isSafeInteger(x)||!Number.isSafeInteger(y)||x<0||y<0||x>=1280||y>=800)throw Error("INVALID_POINT");};
  if(["move","click","drag"].includes(action))point(args.x,args.y);
  if(action==="click"&&!["left","right","middle"].includes(args.button))throw Error("INVALID_BUTTON");
  if(action==="drag")point(args.to_x,args.to_y);
  if(action==="scroll"&&(!Number.isSafeInteger(args.steps)||args.steps===0||Math.abs(args.steps)>20))throw Error("INVALID_SCROLL");
  if(action==="press"&&!key(args.key))throw Error("INVALID_KEY");
  if(action==="hotkey"&&(!Array.isArray(args.keys)||args.keys.length<1||args.keys.length>4||new Set(args.keys).size!==args.keys.length||!args.keys.every(key)))throw Error("INVALID_HOTKEY");
  if(action==="type"&&(typeof args.text!=="string"||args.text.length<1||args.text.length>256||/[\u0000-\u001f\u007f-\u009f]/.test(args.text)||[...args.text].some(c=>{const n=c.codePointAt(0);return n>=0xd800&&n<=0xdfff;})))throw Error("INVALID_TEXT");
 }
 return {validate,id};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=OmniActionPolicy;else globalThis.OmniActionPolicy=OmniActionPolicy;
