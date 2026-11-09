'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const delivery=require('./perplexity_delivery.js');

globalThis.OmniTextDelivery={screenshotFile:(image,id)=>({name:`omni-${id}.png`,size:128,type:'image/png'})};
globalThis.DataTransfer=class{
 constructor(){this._files=[];this.items={add:file=>this._files.push(file)};}
 get files(){return this._files;}
};

function element({attrs={},children=[],text=''}={}){
 const classes=new Set(String(attrs.class||'').split(/\s+/).filter(Boolean));
 const queries=new Map();
 const node={
  attrs,children,isConnected:true,textContent:text,
  classList:{contains:name=>classes.has(name)},
  getClientRects:()=>[{}],
  getAttribute:name=>Object.prototype.hasOwnProperty.call(attrs,name)?attrs[name]:null,
  querySelectorAll(selector){return queries.get(selector)||[];},
  querySelector(selector){return (queries.get(selector)||[])[0]||null;},
  closest(){return null;},
 };
 node.setQuery=(selector,values)=>queries.set(selector,values);
 return node;
}

function observation(id){
 return {
  completed_action:'move',observation_id:id,observed_at_ms:1,observation_ttl_ms:60000,
  coord_space:'image_pixels',width:1280,height:720,source_width:3840,source_height:2160,
  mime:'image/png',
 };
}

function buildDocument(attachmentCount){
 const editor=element({attrs:{contenteditable:'true',role:'textbox'}});
 editor.focus=()=>{};
 editor.addEventListener=()=>{};
 editor.removeEventListener=()=>{};
 const composer=element();
 const scope=element();
 editor.parentElement=composer;
 composer.parentElement=scope;
 const send=element({attrs:{'aria-label':'Invia'}});
 composer.setQuery('button[aria-label="Invia"]',[send]);
 const fileInput={accept:'image/png',files:null,dispatchEvent(){}};
 const preview=element({tag:'img'});
 preview.complete=true;preview.naturalWidth=64;preview.naturalHeight=64;preview.currentSrc='blob:preview';
 const attached=element({tag:'img'});
 attached.complete=true;attached.naturalWidth=64;attached.naturalHeight=64;attached.currentSrc='blob:attached';
 const bubble=element({attrs:{class:'group/user-bubble'}});
 const attachments=element({attrs:{class:'flex-wrap'}});
 attachments.setQuery('img',attachmentCount?[attached]:[]);
 const message=element({attrs:{class:'flex-col'}});
 message.children=[attachments,bubble];
 message.setQuery('[class~="group/user-bubble"]',[bubble]);
 message.setQuery('[data-workflow-final-text],[contenteditable="true"]',[]);
 bubble.parentElement=message;
 const state={sent:false};
 send.click=()=>{state.sent=true;editor.textContent='';};
 const doc={
  querySelectorAll(selector){
   if(selector==='[contenteditable="true"][role="textbox"]')return [editor];
   if(selector==='input[type="file"]')return [fileInput];
   if(selector==='img')return state.sent?[preview]:[];
   if(selector==='[aria-busy="true"],[role="progressbar"]')return [];
   if(selector==='[role="alert"]')return [];
   if(selector==='[class~="group/user-bubble"]')return state.sent?[bubble]:[];
   return [];
  },
  createRange:()=>({selectNodeContents(){},collapse(){}}),
  defaultView:{
   getSelection:()=>({removeAllRanges(){},addRange(){}}),
   getComputedStyle:()=>({pointerEvents:'auto'}),
  },
  execCommand:(command,_,text)=>{editor.textContent=text;return true;},
 };
 fileInput.dispatchEvent=()=>{scope.setQuery('img',[preview]);};
 return {doc,send:()=>state.sent};
}

test('sibling attachment beside outgoing bubble is recognized once',async()=>{
 const env=buildDocument(1);
 const result=await delivery.deliver({
  image:observation('sibling-1'),id:'sibling-1',
  isActive:()=>true,show:()=>{},
 },env.doc);
 assert.equal(result.state,'SENT_WITH_ATTACHMENT_OBSERVED');
 assert.equal(result.request_id,'sibling-1');
 assert.equal(env.send(),true);
});

test('missing sibling attachment halts without retry',async()=>{
 const env=buildDocument(0);
 await assert.rejects(delivery.deliver({
  image:observation('sibling-0'),id:'sibling-0',
  isActive:()=>true,show:()=>{},
 },env.doc),/SEND_UNCERTAIN_HALT_NO_RETRY:req=sibling-0:phase=post_click:ATTACHMENT_COUNT_0/);
 assert.equal(env.send(),true);
});
