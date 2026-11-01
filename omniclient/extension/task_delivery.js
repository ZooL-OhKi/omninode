"use strict";
const OmniTaskDelivery=(()=>{
 async function bounded(operation,ms){let timer;try{return await Promise.race([Promise.resolve().then(operation),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error("TASK_DELIVERY_TIMEOUT")),ms);})]);}finally{clearTimeout(timer);}}
 async function comparePixels(image,preview,doc){
  if(!preview?.complete||preview.naturalWidth<1||preview.naturalHeight<1)throw Error("PREVIEW_NOT_READY");
  const reference=new doc.defaultView.Image();reference.src=image.data_url;await reference.decode();
  const w=preview.naturalWidth,h=preview.naturalHeight;
  if(w>1280||h>800||w<Math.min(64,reference.naturalWidth)||h<Math.min(64,reference.naturalHeight)||w*reference.naturalHeight!==h*reference.naturalWidth)throw Error("PREVIEW_GEOMETRY_UNCERTAIN");
  const pixels=element=>{const canvas=doc.createElement("canvas");canvas.width=w;canvas.height=h;const ctx=canvas.getContext("2d",{willReadFrequently:true});if(!ctx)throw Error("PIXEL_READ_UNAVAILABLE");ctx.drawImage(element,0,0,w,h);return ctx.getImageData(0,0,w,h).data;};
  const expected=pixels(reference),actual=pixels(preview);
  if(expected.length!==actual.length)return false;
  for(let i=0;i<expected.length;i++)if(expected[i]!==actual[i])return false;
  return true;
 }
 async function run(ledger,r,io,options={}){
  if(r.taskDeliveryStarted||r.cancelled||r.image?.auto_delivery!==true||r.image?.completed_action!=="notepad_write")return r;
  r.taskDeliveryStarted=true;
  const wait=options.wait??(ms=>new Promise(resolve=>setTimeout(resolve,ms)));
  const started=ledger.clock(),deadline=started+18000,monotonic=options.monotonic??(()=>performance.now()),monotonicDeadline=monotonic()+18000;
  const alive=()=>!r.cancelled&&ledger.isActive();
  try{
   await bounded(()=>ledger.autoDeliver(r.id,io),5000);
   if(r.state!=="INSERTED")return r;
   while(alive()&&r.state==="INSERTED"&&r.attachment==="ATTACHMENT_PENDING"&&ledger.clock()<deadline&&monotonic()<monotonicDeadline){ledger.observe(r,io);if(r.attachment==="ATTACHMENT_PENDING")await wait(100);}
   if(!alive()){ledger.abort(r);return r;}
   ledger.observe(r,io);
   if(r.state!=="INSERTED"||r.attachment!=="ATTACHMENT_READY_FOR_CONFIRM")throw Error("ATTACHMENT_UNCERTAIN");
   const before=io.attachmentEvidence(r);
   r.busy=true;
   try{
    if(!await bounded(()=>io.verifyPixels(r),5000))throw Error("ATTACHMENT_PIXELS_MISMATCH");
    if(!await bounded(()=>ledger.authorize(),5000)||!alive())throw Error("STALE_TASK_DELIVERY");
    ledger.observe(r,io);
    const after=io.attachmentEvidence(r),current=io.inspect();
    if(r.state!=="INSERTED"||r.attachment!=="ATTACHMENT_READY_FOR_CONFIRM"||after.signature!==before.signature||current.editor!==r.editor||current.text!==r.snapshot)throw Error("COMPOSER_CHANGED");
    r.attachment="ATTACHMENT_VERIFIED";r.attachmentVerification="pixel-match";r.reason=null;
   }finally{r.busy=false;}
   await bounded(()=>ledger.send(r.id,io),5000);
   if(r.state==="INSERTED"&&!r.sendAttempted)throw Error("COMPOSER_NOT_READY");
  }catch(error){
   r.cancelled=true;r.reason=error.message||"AUTOMATIC_DELIVERY_FAILED";
   if(r.sendAttempted)r.state="SEND_UNCERTAIN_HALT";
   else{r.attachment="ATTACHMENT_UNCERTAIN_HALT";if(r.state!=="DRAFT_PROTECTED_HOLD")r.state="ABORTED_SESSION_CHANGE";}
  }
  return r;
 }
 return {run,comparePixels};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=OmniTaskDelivery;else globalThis.OmniTaskDelivery=OmniTaskDelivery;
