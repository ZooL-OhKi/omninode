'use strict';
const OmniPerplexityDelivery=(()=>{
 const visible=x=>Boolean(x?.isConnected&&x.getClientRects().length);
 const read=editor=>(editor.textContent||'').trim();
 const source=x=>x.currentSrc||x.src||'';
 function imageBaseline(doc){return new Set([...doc.querySelectorAll('img')].map(source).filter(Boolean));}
 function previewCandidates(doc,baseline){return [...doc.querySelectorAll('img')].filter(x=>visible(x)&&x.complete&&x.naturalWidth>0&&x.naturalHeight>0&&source(x)&&!baseline.has(source(x))&&!x.closest('[data-workflow-final-text],[class~="group/user-bubble"]'));}
 function sendReady({fileAssigned,previewReady,loading,alert,buttonReady}){return fileAssigned===true&&previewReady===true&&loading===false&&alert===false&&buttonReady===true;}
 async function insertVerified(editor,text,isActive,doc,options={}){
  const wait=options.wait|| (ms=>new Promise(r=>setTimeout(r,ms)));
  const guard=()=>{if(!isActive())throw Error('INSERT_SESSION_CHANGED');if(!editor.isConnected)throw Error('INSERT_EDITOR_REPLACED');};
  guard();if(read(editor))throw Error('DRAFT_PROTECTED_HOLD');
  let touched=false;const onEdit=e=>{if(e.isTrusted)touched=true;};
  editor.addEventListener('beforeinput',onEdit);
  try{
   editor.focus();guard();if(read(editor)||touched)throw Error('DRAFT_CHANGED');
   const range=doc.createRange(),selection=doc.defaultView.getSelection();
   if(!selection)throw Error('INSERT_SELECTION_UNAVAILABLE');
   range.selectNodeContents(editor);range.collapse(false);selection.removeAllRanges();selection.addRange(range);
   guard();if(read(editor)||touched)throw Error('DRAFT_CHANGED');
   let returned=false,threw=false;
   try{returned=doc.execCommand('insertText',false,text);}catch{threw=true;}
   let stable=0;
   for(let i=0;i<30;i++){
    await wait(100);guard();if(touched)throw Error('DRAFT_CHANGED');
    const actual=read(editor);
    if(actual===text){if(++stable>=3)return {state:'INSERT_VERIFIED',commandReturned:returned,commandThrew:threw};}
    else{stable=0;if(actual)throw Error('INSERT_TEXT_MISMATCH');}
   }
   throw Error(threw?'INSERT_COMMAND_EXCEPTION':returned?'INSERT_NOT_OBSERVED':'INSERT_COMMAND_REJECTED');
  }finally{editor.removeEventListener('beforeinput',onEdit);}
 }
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
  if(read(editor)||images().length||loading()||alerts()||input.files?.length)fail('DRAFT_PROTECTED_HOLD');
  const text=JSON.stringify({omninode_response:true,request_id:id,status:'ok',completed_action:'screenshot',width:image.width,height:image.height});
  const file=OmniTextDelivery.screenshotFile(image,id);
  const before=new Set(doc.querySelectorAll('[class~="group/user-bubble"]'));
  show('OmniNode: inserimento risultato; verifica composer.');
  await insertVerified(editor,text,isActive,doc);
  const intact=()=>{guard();if(!editor.isConnected||read(editor)!==text)fail('DRAFT_CHANGED');};
  intact();if(images().length||input.files?.length||loading()||alerts())fail('ATTACHMENT_CHANGED');
  const baseline=imageBaseline(doc);
  const transfer=new DataTransfer();transfer.items.add(file);
  input.files=transfer.files;
  const fileAssigned=input.files.length===1&&input.files[0].name===file.name&&input.files[0].size===file.size&&input.files[0].type===file.type;
  if(!fileAssigned)fail('FILE_ASSIGNMENT_FAILED');
  show('OmniNode: caricamento screenshot; attesa anteprima e prontezza invio.');
  input.dispatchEvent(new Event('change',{bubbles:true,composed:true}));
  let preview=null,send=null,signature='',stable=0,candidateCount=0;
  const readyButtons=()=>[...scope.querySelectorAll('button[aria-label="Invia"]')].filter(x=>visible(x)&&!x.disabled&&x.getAttribute('aria-disabled')!=='true'&&doc.defaultView.getComputedStyle(x).pointerEvents!=='none');
  // This is local UI readiness, not proof of HTTP upload completion.
  for(let i=0;i<300;i++){
   await sleep(100);intact();if(alerts())fail('UPLOAD_ALERT');
   const list=previewCandidates(doc,baseline);candidateCount=list.length;
   const img=list.length===1?list[0]:null,buttons=readyButtons();
   if(buttons.length>1)fail('SEND_AMBIGUOUS');
   const next=img?JSON.stringify([source(img),img.naturalWidth,img.naturalHeight]):'';
   const ready=sendReady({fileAssigned,previewReady:Boolean(img),loading:loading(),alert:alerts(),buttonReady:buttons.length===1});
   stable=ready&&next===signature&&preview===img&&send===buttons[0]?stable+1:0;
   signature=next;preview=img;send=buttons[0]||null;
   if(stable>=10)break;
  }
  if(stable<10||!preview||!send)fail('UPLOAD_SEND_READY_UNCERTAIN_CANDIDATES_'+candidateCount+'_NO_RETRY');
  intact();
  const finalList=previewCandidates(doc,baseline),finalButtons=readyButtons();
  if(!sendReady({fileAssigned,previewReady:finalList.length===1&&finalList[0]===preview&&JSON.stringify([source(preview),preview.naturalWidth,preview.naturalHeight])===signature,loading:loading(),alert:alerts(),buttonReady:finalButtons.length===1&&finalButtons[0]===send}))fail('ATTACHMENT_CHANGED');
  // One attempt only. An uncertain outcome must never trigger another click.
  send.click();show('OmniNode: invio richiesto; verifica messaggio con allegato.');
  for(let i=0;i<100;i++){
   await sleep(100);guard();
   const outgoing=[...doc.querySelectorAll('[class~="group/user-bubble"]')].filter(x=>!before.has(x)&&[x,...x.querySelectorAll('*')].some(y=>y.textContent.trim()===text));
   if(outgoing.length!==1||read(editor))continue;
   const attached=[...outgoing[0].querySelectorAll('img')].filter(x=>visible(x)&&x.complete&&x.naturalWidth>0);
   if(attached.length===1)return {state:'SENT_WITH_ATTACHMENT_OBSERVED',request_id:id};
  }
  fail('SEND_UNCERTAIN_HALT_NO_RETRY');
 }
 return {accepts,deliver,insertVerified,imageBaseline,previewCandidates,sendReady};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=OmniPerplexityDelivery;else globalThis.OmniPerplexityDelivery=OmniPerplexityDelivery;
