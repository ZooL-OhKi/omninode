(() => {
 'use strict';
 if(globalThis.__omniPerplexityAdapter)return;
 globalThis.__omniPerplexityAdapter=true;
 let session=null,busy=false;
 const seen=new Set(),historical=new Set(),pending=new WeakSet();
 const selector='[data-workflow-final-text]';
 const current=()=>location.origin+location.pathname;
 const active=s=>s&&session===s&&Date.now()<s.expires_at&&current()===s.conversation;
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 const host=document.createElement('div');
 host.style.cssText='position:fixed;bottom:12px;right:12px;z-index:2147483647';
 const shadow=host.attachShadow({mode:'closed'}),label=document.createElement('div');
 label.style.cssText='background:#18212f;color:white;padding:10px;border-radius:8px;font:12px system-ui;max-width:360px';
 shadow.append(label);document.documentElement.append(host);
 const show=t=>{label.textContent=t;};
 const signature=p=>p.textContent;
 async function deliver(text,s){
  if(!active(s))return false;
  const composers=Array.from(document.querySelectorAll('[contenteditable="true"][role="textbox"]')).filter(x=>x.getClientRects().length);
  if(composers.length!==1)return false;
  const c=composers[0];if(c.textContent.trim()||c.querySelector('img'))return false;
  c.focus();if(!document.execCommand('insertText',false,text))return false;
  for(let i=0;i<20;i++){
   if(!active(s)||c.textContent.trim()!==text)return false;
   const buttons=Array.from(document.querySelectorAll('button[aria-label="Invia"]')).filter(x=>x.getClientRects().length&&!x.disabled);
   if(buttons.length===1){
    buttons[0].click();
    for(let j=0;j<30;j++){await sleep(100);if(!active(s))return false;if(!c.textContent.trim())return true;}
    return false;
   }
   await sleep(100);
  }
  return false;
 }
 async function process(p,s){
  if(pending.has(p))return;pending.add(p);
  let last='',stable=0;
  for(let i=0;i<120;i++){
   await sleep(500);if(!active(s)||!p.isConnected)return;
   const text=signature(p);stable=text===last?stable+1:0;last=text;
   if(omniIsCompleted(p)&&stable>=3)break;
   if(i===119){show('OmniNode: completamento non confermato; nessuna azione.');return;}
  }
  if(!active(s)||historical.has(signature(p)))return;
  const command=omniParseCommand(omniExtractResponseText(p),globalThis.OmniActionPolicy);
  if(!command||seen.has(command.request_id))return;
  if(busy){show('OmniNode: richiesta concorrente ignorata.');return;}
  if(seen.size>=500){session=null;show('OmniNode: limite richieste raggiunto.');return;}
  seen.add(command.request_id);busy=true;
  try{
   const response=await chrome.runtime.sendMessage({type:'ai-bridge-request',activation_id:s.activation_id,request_id:command.request_id,issued_at:Date.now(),stream_state:'settled',payload:{action:command.action,args:command.args}});
   if(!active(s))return;
   if(response?.ok!==true||response.request_id!==command.request_id||response.activation_id!==s.activation_id)throw Error(response?.code||'RESULT_CORRELATION_FAILED');
   const text=omniBuildResultMessage(command,response);
   show('OmniNode: screenshot ricevuto; immagine non allegata.');
   const sent=await deliver(text,s);
   if(active(s))show(sent?'OmniNode: conferma testuale inviata; immagine non allegata.':'OmniNode: screenshot ricevuto; consegna non confermata, nessun retry.');
  }catch(e){if(active(s))show('OmniNode: '+e.message+'; nessun retry.');}
  finally{busy=false;}
 }
 const observer=new MutationObserver(()=>{const s=session;if(active(s))document.querySelectorAll(selector).forEach(p=>process(p,s));});
 chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(m?.type!=='omninode-activation')return false;
  if(sender.id!==chrome.runtime.id||!/^[a-f0-9]{64}$/.test(m.activation_id||'')||!Number.isSafeInteger(m.expires_at)||m.expires_at<=Date.now()||m.conversation!==current()){reply({ok:false});return false;}
  observer.disconnect();session=m;
  document.querySelectorAll(selector).forEach(p=>{pending.add(p);historical.add(signature(p));});
  chrome.runtime.sendMessage({type:'bridge-bind',activation_id:m.activation_id}).then(r=>{
   if(!active(m)||r?.ok!==true||r.activation_id!==m.activation_id){reply({ok:false});return;}
   observer.observe(document.body,{childList:true,subtree:true,characterData:true});
   show('OmniNode: collegato; screenshot dalle nuove risposte. Immagine non allegata alla chat.');reply({ok:true});
  }).catch(()=>{if(session===m)session=null;reply({ok:false});});return true;
 });
 setInterval(()=>{if(session&&!active(session)){session=null;observer.disconnect();show('OmniNode: sessione terminata.');chrome.runtime.sendMessage({type:'desktop-stop'}).catch(()=>{});}},500);
})();
