"use strict";
class DeliveryLedger {
  constructor(isActive,authorize,records=new Map(),clock=Date.now){this.isActive=isActive;this.authorize=authorize;this.records=records;this.clock=clock;}
  prepare(id,image){
    if(!this.isActive())throw Error("STALE_RESULT");
    if(this.records.has(id))throw Error("DUPLICATE_RESULT");
    const text=JSON.stringify({omninode_response:true,request_id:id,status:"ok",completed_action:"screenshot",width:image.width,height:image.height,bytes:image.bytes,mime:image.mime});
    const r={id,text,image,attachmentAttempted:false,attachmentRequired:false,state:"PREPARED",attachment:"NONE",sendAttempted:false,busy:false,editor:null,snapshot:null};this.records.set(id,r);return r;
  }
  abort(r){r.state=r.sendAttempted?"SEND_UNCERTAIN_HALT":"ABORTED_SESSION_CHANGE";}
  abortAll(){for(const r of this.records.values())if(!["SENT_CONFIRMED","SEND_UNCERTAIN_HALT"].includes(r.state))this.abort(r);}
  async insert(id,io){
    const r=this.records.get(id);if(!r||r.busy||!["PREPARED","DRAFT_PROTECTED_HOLD"].includes(r.state))return;
    r.busy=true;
    try{
      if(!this.isActive()){this.abort(r);return;}
      const first=io.inspect();
      if(!first.editor||first.hasText||first.attachments||first.uploading){r.state="DRAFT_PROTECTED_HOLD";return;}
      if(!await this.authorize()||!this.isActive()){this.abort(r);return;}
      const current=io.inspect();
      if(current.editor!==first.editor||current.hasText||current.attachments||current.uploading){r.state="DRAFT_PROTECTED_HOLD";return;}
      r.editor=current.editor;
      io.insert(r.editor,r.text);
      const after=io.inspect();
      if(!this.isActive()){this.abort(r);return;}
      if(after.editor!==r.editor||after.text.trim()!==r.text){r.state="USER_MODIFIED_ABORT";return;}
      r.snapshot=after.text;r.state="INSERTED";
    }catch{r.state="USER_MODIFIED_ABORT";}finally{r.busy=false;}
  }
  observe(r,io){
    if(["SENT_CONFIRMED","SEND_UNCERTAIN_HALT","ABORTED_SESSION_CHANGE","USER_MODIFIED_ABORT"].includes(r.state))return;
    if(!this.isActive()){this.abort(r);return;}
    try{
      const current=io.inspect();
      if(r.state==="INSERTED"&&(current.editor!==r.editor||current.text!==r.snapshot))r.state="USER_MODIFIED_ABORT";
      if(r.state==="INSERTED"&&r.attachmentRequired)this.observeAttachment(r,io);
      if(r.state==="SEND_REQUESTED"){
        const proof=io.evidence(r,r.before);
        if(proof.composerEmpty&&proof.outgoingExact&&proof.generationObserved&&(!r.attachmentRequired||proof.outgoingAttachment===true))r.state="SENT_CONFIRMED";
        else if(this.clock()-r.sentAt>=10000)r.state="SEND_UNCERTAIN_HALT";
      }
    }catch{r.state=r.sendAttempted?"SEND_UNCERTAIN_HALT":"USER_MODIFIED_ABORT";}
  }
  async attach(id,io){
    const r=this.records.get(id);if(!r||r.busy||r.sendAttempted||r.state!=="INSERTED"||r.attachmentAttempted)return;
    r.busy=true;r.attachmentRequired=true;
    try{
      if(!this.isActive()||!await this.authorize()||!this.isActive()){this.abort(r);return;}
      this.observe(r,io);if(r.state!=="INSERTED")return;
      const x=io.inspect();if(x.attachments||x.uploading){r.reason="EXISTING_ATTACHMENT_HOLD";return;}
      if(!io.canPaste()){r.attachment="ATTACHMENT_ASSISTED_REQUIRED";return;}
      const file=io.makeFile(r.image,r.id);r.uploadBaseline=io.uploadBaseline();
      if(!this.isActive()){this.abort(r);return;}
      r.reason=null;r.attachmentAttempted=true;r.attachment="ATTACHMENT_PENDING";r.uploadStarted=this.clock();
      io.pasteFile(r.editor,file);
    }catch{r.attachment=r.attachmentAttempted?"ATTACHMENT_UNCERTAIN_HALT":"ATTACHMENT_FAILED_HOLD";}
    finally{r.busy=false;}
  }
  observeAttachment(r,io){
    if(!["ATTACHMENT_PENDING","ATTACHMENT_READY_FOR_CONFIRM","ATTACHMENT_VERIFIED"].includes(r.attachment))return;
    const e=io.attachmentEvidence(r);
    const ready=e.count===1&&e.loaded===true&&!e.uploading&&!e.error;
    if(r.attachment==="ATTACHMENT_VERIFIED"){
      if(!ready||e.signature!==r.attachmentSignature)r.attachment="ATTACHMENT_UNCERTAIN_HALT";
      return;
    }
    if(!ready){r.readySince=null;r.attachmentSignature=null;r.attachment="ATTACHMENT_PENDING";if(this.clock()-r.uploadStarted>=15000)r.attachment="ATTACHMENT_UNCERTAIN_HALT";return;}
    if(r.attachmentSignature!==e.signature){r.attachmentSignature=e.signature;r.readySince=this.clock();r.attachment="ATTACHMENT_PENDING";return;}
    if(this.clock()-r.readySince>=3000)r.attachment="ATTACHMENT_READY_FOR_CONFIRM";
  }
  async confirmAttachment(id,io){
    const r=this.records.get(id);if(!r||r.busy||r.state!=="INSERTED"||r.attachment!=="ATTACHMENT_READY_FOR_CONFIRM")return;
    r.busy=true;
    try{
      if(!this.isActive()||!await this.authorize()||!this.isActive()){this.abort(r);return;}
      this.observe(r,io);
      if(r.state==="INSERTED"&&r.attachment==="ATTACHMENT_READY_FOR_CONFIRM"){r.reason=null;r.attachment="ATTACHMENT_VERIFIED";r.attachmentVerification="user-confirmed";}
    }catch{r.attachment="ATTACHMENT_UNCERTAIN_HALT";}finally{r.busy=false;}
  }
  async send(id,io){
    const r=this.records.get(id);if(!r||r.busy||r.sendAttempted||r.state!=="INSERTED")return;
    r.busy=true;
    try{
      if(!this.isActive()||!await this.authorize()||!this.isActive()){this.abort(r);return;}
      this.observe(r,io);if(r.state!=="INSERTED")return;
      const current=io.inspect();
      if((r.attachmentRequired?r.attachment!=="ATTACHMENT_VERIFIED":current.attachments)||current.uploading||!current.sendEnabled){r.reason="COMPOSER_NOT_READY";return;}
      r.before=io.baseline();r.sendAttempted=true;r.sentAt=this.clock();r.state="SEND_REQUESTED";
      io.clickSend(current.sendButton);
    }catch{r.state=r.sendAttempted?"SEND_UNCERTAIN_HALT":"ABORTED_SESSION_CHANGE";}
    finally{r.busy=false;}
  }
}
// Input comes from bridge_result.js; this checks transport bounds, not full codec validity.
function screenshotFile(image,id,FileType=File){
  if(!/^[A-Za-z0-9._-]{8,128}$/.test(id)||!["image/png","image/jpeg"].includes(image.mime)||!Number.isSafeInteger(image.width)||!Number.isSafeInteger(image.height)||!Number.isSafeInteger(image.bytes)||image.width<1||image.height<1||image.width>1280||image.height>800)throw Error("INVALID_IMAGE");
  const prefix="data:"+image.mime+";base64,";
  if(typeof image.data_url!=="string"||!image.data_url.startsWith(prefix))throw Error("INVALID_IMAGE");
  const encoded=image.data_url.slice(prefix.length);if(encoded.length>819200)throw Error("IMAGE_TOO_LARGE");
  const binary=atob(encoded);if(!binary.length||binary.length>614400||binary.length!==image.bytes||btoa(binary)!==encoded)throw Error("INVALID_IMAGE");
  const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
  return new FileType([bytes],"omninode-"+id+(image.mime==="image/jpeg"?".jpg":".png"),{type:image.mime});
}
function mountTextDelivery(session,image,id,box,options){
  const ledger=session.deliveryController || (session.deliveryController=new DeliveryLedger(options.isActive,options.authorize,session.deliveryLedger));
  const r=ledger.prepare(id,image),doc=box.ownerDocument;
  const available=el=>Boolean(el&&el.isConnected&&!el.disabled&&el.getAttribute("aria-disabled")!=="true"&&el.getClientRects().length&&(!el.checkVisibility||el.checkVisibility({opacityProperty:true,visibilityProperty:true})));
  function inspect(){
    const candidates=[...doc.querySelectorAll('input-area-v2 fieldset rich-textarea [contenteditable="true"]')].filter(available);
    const preferred=options.getEditor();const editor=candidates.includes(preferred)?preferred:(candidates.length===1?candidates[0]:null);
    if(!editor)return {editor:null,hasText:true,attachments:true,uploading:false,text:"",sendEnabled:false};
    const scope=editor.closest("input-area-v2"),fieldset=editor.closest("fieldset");
    const text=editor.innerText??editor.textContent??"";
    const hasText=Boolean(text.replace(/[\u200B-\u200D\uFEFF]/g,"").trim());
    const attachments=[...scope.querySelectorAll('img,canvas,video,audio,[data-test-id*="attachment"],[data-test-id*="file-preview"]')].some(available)||[...scope.querySelectorAll('*')].some(el=>/(attachment|file-preview|chip)/i.test(el.localName)&&available(el))||[...scope.querySelectorAll('input[type="file"]')].some(el=>el.files?.length);
    const uploading=[...scope.querySelectorAll('[aria-busy="true"],[role="progressbar"],mat-spinner,mat-progress-spinner,mat-progress-bar')].some(available);
    const sends=[...fieldset.querySelectorAll('button[aria-label="Invia messaggio"],button[aria-label="Send message"],button[data-test-id="send-button"]')].filter(available);
    return {editor,scope,text,hasText,attachments,uploading,sendButton:sends.length===1?sends[0]:null,sendEnabled:sends.length===1};
  }
  const previews=scope=>[...(scope?.querySelectorAll("img")||[])].filter(available);
  const io={inspect,canPaste:()=>typeof DataTransfer==="function"&&typeof ClipboardEvent==="function",makeFile:screenshotFile,
  uploadBaseline(){return new Set(previews(inspect().scope));},
  pasteFile(editor,file){const x=inspect();if(x.editor!==editor||x.text!==r.snapshot||x.attachments||x.uploading)throw Error("COMPOSER_CHANGED");const data=new DataTransfer();data.items.add(file);editor.dispatchEvent(new ClipboardEvent("paste",{clipboardData:data,bubbles:true,cancelable:true,composed:true}));},
  attachmentEvidence(record){const x=inspect(),all=previews(x.scope),fresh=all.filter(el=>!record.uploadBaseline.has(el));const img=fresh.length===1?fresh[0]:null;return {count:all.length===1?fresh.length:0,loaded:Boolean(img?.complete&&img.naturalWidth>0&&img.naturalHeight>0),uploading:x.uploading,error:Boolean(x.scope&&[...x.scope.querySelectorAll('[role="alert"]')].some(available)),signature:img?JSON.stringify([img.currentSrc||img.src,img.naturalWidth,img.naturalHeight]):null};},
  insert(editor,text){
    editor.focus();const current=inspect();if(current.editor!==editor||current.hasText||current.attachments||current.uploading)throw Error("DRAFT_CHANGED");
    const range=doc.createRange();range.selectNodeContents(editor);range.collapse(false);
    const selection=doc.defaultView.getSelection();selection.removeAllRanges();selection.addRange(range);
    if(!doc.execCommand("insertText",false,text))throw Error("INSERT_UNSUPPORTED");
  },clickSend(button){button.click();},baseline(){return {queries:new Set(doc.querySelectorAll("user-query")),models:new Set(doc.querySelectorAll("model-response"))};},evidence(record,before){
    const current=inspect();
    const outgoingExact=[...doc.querySelectorAll("user-query")].some(node=>!before.queries.has(node)&&[node,...node.querySelectorAll("*")].some(el=>(el.textContent||"").trim()===record.text));
    const generationObserved=[...doc.querySelectorAll("model-response")].some(node=>!before.models.has(node))||Boolean(doc.querySelector('button[data-test-id="stop-button"],button[aria-label="Interrompi risposta"],button[aria-label="Stop response"]'));
    const outgoingAttachment=[...doc.querySelectorAll("user-query")].some(node=>!before.queries.has(node)&&node.querySelector("img")&&[node,...node.querySelectorAll("*")].some(el=>(el.textContent||"").trim()===record.text));
    return {composerEmpty:current.editor===record.editor&&!current.hasText,outgoingExact,generationObserved,outgoingAttachment};
  }};
  const state=doc.createElement("div"),insert=doc.createElement("button"),send=doc.createElement("button"),download=doc.createElement("button"),payload=doc.createElement("textarea"),diagnostic=doc.createElement("button");
  insert.textContent="Inserisci risultato testuale";send.textContent="Invia risultato testuale (un tentativo, senza immagine)";download.textContent="Scarica screenshot per allegarlo manualmente";diagnostic.textContent="Diagnostica composer (sola lettura)";
  const attach=doc.createElement("button"),verify=doc.createElement("button");
  attach.textContent="Inserisci risultato e allega screenshot a Gemini (condivide l'immagine)";
  verify.textContent="yes — confermo screenshot nell'input Gemini, upload concluso e autorizzo l'invio";
  box.append(attach,verify);
  payload.readOnly=true;payload.value=r.text;box.append(state,insert,send,download,diagnostic,payload);
  function refresh(){ledger.observe(r,io);state.textContent=r.state+" — "+r.attachment+(r.attachmentVerification?" (conferma utente)":"")+(r.reason?" — "+r.reason:"");insert.disabled=r.busy||!["PREPARED","DRAFT_PROTECTED_HOLD"].includes(r.state);send.textContent=r.attachmentRequired?"Invia testo e immagine confermata (un tentativo)":"Invia risultato testuale (un tentativo, senza immagine)";send.disabled=r.busy||r.state!=="INSERTED"||r.sendAttempted||(r.attachmentRequired&&r.attachment!=="ATTACHMENT_VERIFIED");attach.disabled=r.busy||!["PREPARED","DRAFT_PROTECTED_HOLD","INSERTED"].includes(r.state)||r.attachmentAttempted||r.sendAttempted;verify.hidden=r.attachment!=="ATTACHMENT_READY_FOR_CONFIRM";verify.disabled=r.busy;download.disabled=!options.isActive();}
  attach.addEventListener("click",async e=>{if(!e.isTrusted)return;await ledger.insert(id,io);await ledger.attach(id,io);refresh();});
  verify.addEventListener("click",async e=>{if(!e.isTrusted)return;await ledger.confirmAttachment(id,io);if(r.attachment==="ATTACHMENT_VERIFIED")await ledger.send(id,io);refresh();});
  insert.addEventListener("click",async e=>{if(!e.isTrusted)return;await ledger.insert(id,io);refresh();});
  send.addEventListener("click",async e=>{if(!e.isTrusted)return;await ledger.send(id,io);refresh();});
  download.addEventListener("click",e=>{if(!e.isTrusted||!options.isActive())return;const a=doc.createElement("a");a.href=image.data_url;a.download="omninode-"+id+(image.mime==="image/jpeg"?".jpg":".png");a.click();if(!r.attachmentAttempted)r.attachment="ATTACHMENT_ASSISTED_REQUIRED";state.textContent=r.state+" — allegato manuale non verificato; nessun upload automatico";});
  diagnostic.addEventListener("click",e=>{if(!e.isTrusted)return;const x=inspect();payload.value=JSON.stringify({diagnostic:"omninode-delivery-composer-v1",editorFound:Boolean(x.editor),hasText:x.hasText,attachments:x.attachments,uploading:x.uploading,sendEnabled:x.sendEnabled,attachmentState:r.attachment,attachmentAttempted:r.attachmentAttempted});});
  const timer=setInterval(()=>{refresh();if(!options.isActive()||["SENT_CONFIRMED","SEND_UNCERTAIN_HALT","ABORTED_SESSION_CHANGE","USER_MODIFIED_ABORT"].includes(r.state))clearInterval(timer);},250);
  refresh();return r;
}
const OmniTextDelivery={DeliveryLedger,mountTextDelivery,screenshotFile};
if(typeof module!=="undefined"&&module.exports)module.exports=OmniTextDelivery;else globalThis.OmniTextDelivery=OmniTextDelivery;
