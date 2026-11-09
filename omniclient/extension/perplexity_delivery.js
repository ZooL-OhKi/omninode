'use strict';
const OmniPerplexityDelivery=(()=>{
 const visible=x=>Boolean(x?.isConnected&&x.getClientRects().length);
 function accepts(input,mime){const tokens=input.accept.toLowerCase().split(',').map(x=>x.trim());return tokens.includes('image/*')||tokens.includes(mime)||tokens.includes(mime==='image/png'?'.png':'.jpg')||(mime==='image/jpeg'&&tokens.includes('.jpeg'));}
 async function deliver({image,id,isActive,show},doc=document){
  const fail=code=>{throw Error(code);},sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const guard=()=>{if(!isActive())fail('DELIVERY_SESSION_CHANGED');};
  guard();
  const editors=[...doc.querySelectorAll('[contenteditable="true"][role="textbox"]')].filter(visible);
  if(editors.length!==1)fail('COMPOSER_AMBIGUOUS');
  const editor=editors[0];let scope=editor.parentElement;
  for(let depth=0;scope&&depth<7;depth++,scope=scope.parentElement){if(scope.querySelector('button[aria-label="Invia"]'))break;}
  if(!scope||scope===doc.body||scope===doc.documentElement)fail('COMPOSER_SCOPE_UNKNOWN');
  const inputs=[...doc.querySelectorAll('input[type="file"]')];
  if(inputs.length!==1||!accepts(inputs[0],image.mime))fail('IMAGE_INPUT_UNSUPPORTED');
  const input=inputs[0];
  const images=()=>[...scope.querySelectorAll('img')].filter(visible);
  const loading=()=>[...scope.querySelectorAll('[aria-busy="true"],[role="progressbar"]')].some(visible);
  const alerts=()=>[...scope.querySelectorAll('[role="alert"]')].some(visible);
  if(editor.textContent.trim()||images().length||loading()||alerts()||input.files?.length)fail('DRAFT_PROTECTED_HOLD');
  const text=JSON.stringify({omninode_response:true,request_id:id,status:'ok',completed_action:'screenshot',width:image.width,height:image.height});
  const file=OmniTextDelivery.screenshotFile(image,id);
  const before=new Set(doc.querySelectorAll('[class~="group/user-bubble"]'));
  editor.focus();guard();
  if(editor.textContent.trim()||images().length||input.files?.length)fail('DRAFT_CHANGED');
  if(!doc.execCommand('insertText',false,text)||editor.textContent.trim()!==text)fail('RESULT_INSERT_FAILED');
  const intact=()=>{guard();if(!editor.isConnected||editor.textContent.trim()!==text)fail('DRAFT_CHANGED');};
  intact();const transfer=new DataTransfer();transfer.items.add(file);
  input.files=transfer.files;
  if(input.files.length!==1||input.files[0].name!==file.name)fail('FILE_ASSIGNMENT_FAILED');
  show('OmniNode: caricamento screenshot; nessun invio finche non verificato.');
  input.dispatchEvent(new Event('change',{bubbles:true,composed:true}));
  let preview=null,signature='',stable=0;
  for(let i=0;i<150;i++){
   await sleep(100);intact();if(alerts())fail('UPLOAD_ALERT');
   const list=images(),img=list.length===1?list[0]:null;
   const ready=img?.complete&&img.naturalWidth>0&&img.naturalHeight>0&&!loading();
   const next=ready?JSON.stringify([img.currentSrc||img.src,img.naturalWidth,img.naturalHeight]):'';
   stable=next&&next===signature?stable+1:0;signature=next;
   if(stable>=10){preview=img;break;}
  }
  if(!preview)fail('UPLOAD_PREVIEW_UNCERTAIN_NO_RETRY');
  let timer;
  try{const match=await Promise.race([OmniTaskDelivery.comparePixels(image,preview,doc),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('PIXEL_CHECK_TIMEOUT')),5000);})]);if(!match)fail('UPLOAD_PIXELS_MISMATCH');}finally{clearTimeout(timer);}
  intact();
  if(images().length!==1||images()[0]!==preview||loading()||alerts()||JSON.stringify([preview.currentSrc||preview.src,preview.naturalWidth,preview.naturalHeight])!==signature)fail('ATTACHMENT_CHANGED');
  const buttons=[...scope.querySelectorAll('button[aria-label="Invia"]')].filter(x=>visible(x)&&!x.disabled&&x.getAttribute('aria-disabled')!=='true');
  if(buttons.length!==1)fail('SEND_NOT_READY');
  guard();buttons[0].click();show('OmniNode: invio richiesto; verifica messaggio con allegato.');
  for(let i=0;i<100;i++){
   await sleep(100);guard();
   const outgoing=[...doc.querySelectorAll('[class~="group/user-bubble"]')].filter(x=>!before.has(x)&&[x,...x.querySelectorAll('*')].some(y=>y.textContent.trim()===text));
   if(outgoing.length!==1||editor.textContent.trim())continue;
   const attached=[...outgoing[0].querySelectorAll('img')].filter(x=>visible(x)&&x.complete&&x.naturalWidth>0);
   if(attached.length===1)return {state:'SENT_WITH_ATTACHMENT_OBSERVED',request_id:id};
  }
  fail('SEND_UNCERTAIN_HALT_NO_RETRY');
 }
 return {accepts,deliver};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=OmniPerplexityDelivery;else globalThis.OmniPerplexityDelivery=OmniPerplexityDelivery;
