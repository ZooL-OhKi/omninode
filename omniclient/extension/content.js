(() => {
"use strict";
const normalized=t=>String(t??"").replace(/[\u200B-\u200D\uFEFF]/g,"").replace(/\s+/g," ").trim();
function parseRequest(text){const r=JSON.parse(text.trim());if(!r||Array.isArray(r)||Object.keys(r).sort().join(",")!=="action,args,request_id"||r.action!=="screenshot"||typeof r.request_id!=="string"||!/^[A-Za-z0-9._-]{8,128}$/.test(r.request_id)||!r.args||Array.isArray(r.args)||typeof r.args!=="object"||Object.keys(r.args).length)throw Error("INVALID_REQUEST");return r;}
function canDeliver(active,same,streaming,text){return Boolean(active&&same&&!streaming&&normalized(text)==="");}
function prepareResultDelivery(editor,payload,delivered=new Set()){
  if(!payload||typeof payload.request_id!=="string")return {state:"INVALID_RESULT"};
  if(delivered.has(payload.request_id))return {state:"DUPLICATE_RESULT"};
  if(!editor)return {state:"DRAFT_PROTECTED_HOLD"};
  const scope=editor.closest?.("rich-textarea")||editor;
  if(normalized(editor.textContent||editor.value||"")||scope.querySelector?.('[data-test-id*="attachment"], [data-test-id*="file-preview"], img, video, audio')||[...(scope.querySelectorAll?.('input[type="file"]')||[])].some(x=>x.files?.length))return {state:"DRAFT_PROTECTED_HOLD"};
  delivered.add(payload.request_id);
  return {state:"READY_FOR_CONTROLLED_INSERTION",text:JSON.stringify({omninode_result:true,request_id:payload.request_id,status:payload.ok?"ok":"error",result:payload.result??null})};
}
class LiveBirthGate{
  constructor(nodes,activatedAt=0){this.activatedAt=activatedAt;this.baseline=new Set(nodes.map(x=>normalized(x.textContent)));this.ignored=new WeakSet(nodes);this.entries=new WeakMap();}
  added(nodes,last,now){for(const node of nodes){if(now<this.activatedAt||nodes.length!==1||node!==last||this.baseline.has(normalized(node.textContent))||this.ignored.has(node)){this.ignored.add(node);this.entries.delete(node);continue;}if(!this.entries.has(node))this.entries.set(node,{state:"OBSERVING_MUTATIONS",live:false,since:null,ticks:0,signature:null});}}
  mutation(node,live=true){const c=this.entries.get(node);if(c){c.live=c.live||live;c.state="OBSERVING_MUTATIONS";c.since=null;c.ticks=0;c.signature=null;}}
  sample(node,signal,now){
    const c=this.entries.get(node);if(!c||this.ignored.has(node))return "BASELINE_IGNORED";
    if(signal.blockCount>1){this.ignored.add(node);c.state="REJECTED_MULTI_BLOCK";return c.state;}
    const signature=JSON.stringify([signal.text,signal.controls]);
    if(!c.live||signal.streaming||!signal.complete||!signal.valid||signal.blockCount!==1){c.state="OBSERVING_MUTATIONS";c.since=null;c.ticks=0;c.signature=null;return c.state;}
    if(c.signature!==null&&c.signature!==signature){c.signature=null;c.since=null;c.ticks=0;c.state="OBSERVING_MUTATIONS";return c.state;}
    if(c.signature!==signature){c.signature=signature;c.since=now;c.ticks=1;c.state="COMPLETION_BAR_READY";return c.state;}
    c.ticks++;c.state=now-c.since>=3000&&c.ticks>=2?"SETTLED":"COMPLETION_BAR_READY";return c.state;
  }
}
class OneShotGate{
  constructor(){this.turn=null;this.used=new Set();}
  arm(turn){this.turn=turn;}
  allow(turn,id,confirmed=false){if(this.used.has(id)||(!confirmed&&this.turn!==turn))return false;this.turn=null;this.used.add(id);return true;}
}
function isSettled(s,ms){return s.streaming===false&&s.completionReady===true&&ms>=3000;}
if(typeof module!=="undefined"&&module.exports){module.exports={parseRequest,canDeliver,isSettled,prepareResultDelivery,LiveBirthGate,OneShotGate};return;}
if(globalThis.__omninodeBridge)return;globalThis.__omninodeBridge=true;
// Disabled until real provider completion controls and lifecycle are validated.
const COMPLETION_SELECTORS=Object.freeze([]);
const STOP_SELECTOR='button[data-test-id="stop-button"], button[aria-label="Stop response"], button[aria-label="Interrompi risposta"], button[aria-label="Stop generating"], button[aria-label="Interrompi generazione"]';
let session=null;
const host=document.createElement("div");host.style.cssText="position:fixed;right:18px;bottom:18px;z-index:2147483647";
const shadow=host.attachShadow({mode:"closed"}),panel=document.createElement("div");panel.style.cssText="background:#18212f;color:white;padding:12px;font:13px system-ui;max-width:380px;max-height:70vh;overflow:auto";
const status=document.createElement("div"),resultBox=document.createElement("div"),confirm=document.createElement("button"),arm=document.createElement("button"),diag=document.createElement("button");
arm.textContent="Autorizza richiesta del turno corrente (1-shot)";confirm.hidden=true;diag.textContent="Diagnostica DOM 12 s (sola lettura)";
panel.append(status,arm,confirm,diag,resultBox);shadow.append(panel);document.body.append(host);
const nodes=()=>[...document.querySelectorAll("model-response")];
const visible=el=>el&&!el.disabled&&el.getAttribute("aria-disabled")!=="true"&&el.getClientRects().length>0;
function signals(node){
  const blocks=[...node.querySelectorAll("pre")];let request=null;try{if(blocks.length===1)request=parseRequest(blocks[0].textContent||"");}catch{}
  const controls=COMPLETION_SELECTORS.flatMap(s=>[...node.querySelectorAll(s)].filter(visible).map(()=>s));
  const streaming=Boolean(node.matches('[aria-busy="true"], [data-is-streaming="true"]')||node.querySelector('[aria-busy="true"], [data-is-streaming="true"]')||[...document.querySelectorAll(STOP_SELECTOR)].some(visible));
  return {text:node.textContent||"",controls:controls.join("|"),complete:controls.length>0,streaming,valid:Boolean(request),blockCount:blocks.length,request};
}
function active(s){return session===s&&Date.now()<s.expiresAt&&location.origin+location.pathname===s.conversation;}
function localStop(text){session=null;confirm.hidden=true;status.textContent=text;}
const observer=new MutationObserver(records=>{
  const s=session;if(!s||!active(s))return;const added=new Set();
  for(const r of records)for(const el of r.addedNodes){if(el.nodeType!==1)continue;if(el.matches?.("model-response"))added.add(el);for(const n of el.querySelectorAll?.("model-response")||[])added.add(n);}
  s.birth.added([...added],nodes().at(-1),performance.now());
  for(const r of records){const el=r.target.nodeType===1?r.target:r.target.parentElement,n=el?.closest?.("model-response");if(n)s.birth.mutation(n,r.type==="characterData"||(r.type==="childList"&&[...r.addedNodes].some(x=>x.nodeType===3)));}
});
observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:["aria-busy","data-is-streaming","disabled","aria-disabled","class"]});
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(m?.type!=="omninode-activation"||sender.id!==chrome.runtime.id)return false;
  if(typeof m.activation_id!=="string"||!/^[a-f0-9]{64}$/.test(m.activation_id)||m.conversation!==location.origin+location.pathname||!Number.isSafeInteger(m.expires_at)||m.expires_at<=Date.now()){reply({ok:false});return false;}
  const s={activation:m.activation_id,conversation:m.conversation,expiresAt:m.expires_at,birth:new LiveBirthGate(nodes(),performance.now()),gate:new OneShotGate(),delivered:new Set(),pending:null,candidate:null};
  session=s;confirm.hidden=true;resultBox.textContent="";
  chrome.runtime.sendMessage({type:"bridge-bind",activation_id:s.activation}).then(r=>{
    if(!active(s)||!r?.ok||r.activation_id!==s.activation){if(session===s)localStop("Aggancio documento fallito");reply({ok:false});return;}
    status.textContent="Sessione autorizzata. Fine risposta non validata: esecuzione bloccata; disponibile diagnostica 12 s.";reply({ok:true});
  }).catch(()=>{if(session===s)localStop("Aggancio documento fallito");reply({ok:false});});return true;
});
function candidate(s){const node=nodes().at(-1);if(!node)return null;const signal=signals(node);return {node,signal,state:s.birth.sample(node,signal,performance.now())};}
async function execute(s,c,confirmed){
  if(!active(s)||s.pending)return;const fresh=candidate(s);
  if(!fresh||fresh.node!==c.node||fresh.state!=="SETTLED"||JSON.stringify(fresh.signal.request)!==JSON.stringify(c.signal.request))return;
  const r=fresh.signal.request;if(!s.gate.allow(c.node,r.request_id,confirmed))return;
  s.pending=r.request_id;confirm.hidden=true;status.textContent="Esecuzione screenshot autorizzato";
  try{
    const response=await chrome.runtime.sendMessage({type:"ai-bridge-request",activation_id:s.activation,request_id:r.request_id,issued_at:Date.now(),stream_state:"settled",payload:{action:r.action,args:r.args}});
    if(!active(s)||!response||response.activation_id!==s.activation||response.request_id!==s.pending)return;
    s.pending=null;if(!response.ok){localStop(response.rejected?"Richiesta rifiutata: "+response.code:"Errore: sessione terminata");return;}
    resultBox.textContent="";
    if(response.result?.kind==="image"){const img=document.createElement("img");img.src=response.result.data_url;img.style.maxWidth="100%";img.alt="Screenshot autorizzato";resultBox.append(img);}
    const editor=document.querySelector('rich-textarea [contenteditable="true"], textarea');
    const prepared=prepareResultDelivery(editor,{request_id:r.request_id,ok:true,result:{kind:response.result.kind,mime:response.result.mime,width:response.result.width,height:response.result.height,bytes:response.result.bytes}},s.delivered);
    status.textContent=prepared.state+" — nessun inserimento o invio automatico";
    const text=document.createElement("textarea");text.readOnly=true;text.value=prepared.text||JSON.stringify({omninode_result:true,request_id:r.request_id,status:"ok"});resultBox.append(text);
  }catch{if(active(s))localStop("Canale interrotto: nessun retry");}
}
arm.addEventListener("click",e=>{if(!e.isTrusted||!session||!active(session))return;const c=candidate(session);if(!c||!["OBSERVING_MUTATIONS","COMPLETION_BAR_READY"].includes(c.state)){status.textContent="Nessun turno corrente nato vivo da autorizzare";return;}session.gate.arm(c.node);status.textContent="Autorizzazione 1-shot limitata al turno corrente";});
confirm.addEventListener("click",e=>{if(e.isTrusted&&session?.candidate)execute(session,session.candidate,true);});
setInterval(()=>{
  const s=session;if(!s)return;if(!active(s)){localStop("Sessione scaduta o conversazione cambiata");return;}if(s.pending)return;
  const c=candidate(s);if(!c||c.state!=="SETTLED"){confirm.hidden=true;return;}if(s.gate.used.has(c.signal.request.request_id))return;
  s.candidate=c;if(s.gate.turn===c.node){execute(s,c,false);return;}
  status.textContent="PENDING_USER_CONFIRM";confirm.textContent="Esegui screenshot ("+c.signal.request.request_id+")";confirm.hidden=false;
},500);
diag.addEventListener("click",e=>{
  if(!e.isTrusted||diag.disabled)return;diag.disabled=true;const started=performance.now(),samples=[];let previous="";
  const timer=setInterval(()=>{
    const last=nodes().at(-1),buttons=[...(last?.querySelectorAll("button")||[])];
    const controls=buttons.map(b=>({visible:Boolean(visible(b)),testId:/^(?:copy|like|dislike|feedback|response|share|more|menu|stop)[a-z_-]{0,48}$/i.test(b.getAttribute("data-test-id")||"")?b.getAttribute("data-test-id"):null,labelKind:/^(?:copy|copia|good response|bad response|risposta utile|risposta non utile|share|condividi|more|altro|stop|interrompi)(?: message| risposta)?$/i.test(b.getAttribute("aria-label")||"")?b.getAttribute("aria-label"):null}));
    const flag=name=>{const v=last?.getAttribute(name);return v==="true"||v==="false"?v:null;};
    const sample={responses:nodes().length,ariaBusy:flag("aria-busy"),dataIsStreaming:flag("data-is-streaming"),preCount:last?.querySelectorAll("pre").length??0,stopVisible:[...document.querySelectorAll(STOP_SELECTOR)].some(visible),buttons:controls};
    const signature=JSON.stringify(sample);if(signature!==previous){samples.push({elapsedMs:Math.round(performance.now()-started),...sample});previous=signature;}
    if(performance.now()-started>=12000){clearInterval(timer);diag.disabled=false;const text=document.createElement("textarea");text.readOnly=true;text.value=JSON.stringify({diagnostic:"omninode-dom-metadata-v1",durationMs:12000,samples},null,2);resultBox.replaceChildren(text);status.textContent="Diagnostica conclusa: soli metadati; nessuna azione desktop";}
  },250);
});
})();
