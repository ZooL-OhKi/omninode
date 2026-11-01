"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const {DeliveryLedger}=require("./text_delivery.js");
const {parseRequest}=require("./content.js");
const image={mime:"image/png",width:1,height:1,bytes:3,data_url:"data:image/png;base64,QUJD"};
function fixture(options={}){
 const state={active:true,now:0,text:options.initialText??"",inserted:0,clicked:0,pasted:0,attached:false,sent:false};
 const editor={},otherEditor={},sendButton={};
 const ledger=new DeliveryLedger(()=>state.active,async()=>true,new Map(),()=>state.now);
 const io={
  inspect(){const changed=options.changeAfterInsert&&state.inserted>0;const text=changed?"bozza utente":state.text;return {editor:changed?otherEditor:editor,text,hasText:!!text,attachments:state.attached,uploading:false,sendEnabled:true,sendButton};},
  insert(target,text){assert.equal(target,editor);state.text=text;state.inserted++;},
  canPaste(){return options.supported!==false;},
  makeFile(value,id){assert.equal(value,image);return {id};},
  uploadBaseline(){return new Set();},
  pasteFile(target){assert.equal(target,editor);state.pasted++;state.attached=true;},
  attachmentEvidence(){return {count:state.attached?1:0,loaded:state.attached,uploading:false,error:false,signature:state.attached?"preview-1":null};},
  baseline(){return {};},
  clickSend(button){assert.equal(button,sendButton);state.clicked++;state.sent=true;state.text="";state.attached=false;},
  evidence(){return {composerEmpty:state.text==="",outgoingExact:state.sent,generationObserved:state.sent,outgoingAttachment:state.sent};}
 };
 return {state,ledger,io};
}
test("auto delivery preserves an existing user draft",async()=>{
 const {state,ledger,io}=fixture({initialText:"bozza utente"});
 const r=ledger.prepare("draft-hold-001",image);
 assert.equal(await ledger.autoDeliver(r.id,io),r);
 assert.equal(r.state,"DRAFT_PROTECTED_HOLD");
 assert.equal(state.text,"bozza utente");
 assert.equal(state.inserted,0);assert.equal(state.pasted,0);assert.equal(state.clicked,0);
});
test("auto delivery aborts when the user modifies the composer concurrently",async()=>{
 const {state,ledger,io}=fixture({changeAfterInsert:true});
 const r=ledger.prepare("race-hold-001",image);
 await ledger.autoDeliver(r.id,io);
 assert.equal(r.state,"USER_MODIFIED_ABORT");
 assert.equal(io.inspect().text,"bozza utente");
 assert.equal(state.pasted,0);assert.equal(state.clicked,0);
});
test("auto delivery aborts a stale session",async()=>{
 const {state,ledger,io}=fixture();
 const r=ledger.prepare("stale-001",image);state.active=false;
 await ledger.autoDeliver(r.id,io);
 assert.equal(r.state,"ABORTED_SESSION_CHANGE");
 assert.equal(state.inserted,0);assert.equal(state.pasted,0);assert.equal(state.clicked,0);
});
test("authorized image delivery requires confirmation and sends exactly once",async()=>{
 const {state,ledger,io}=fixture();
 const r=ledger.prepare("auto-ok-001",image);
 await Promise.all([ledger.autoDeliver(r.id,io),ledger.autoDeliver(r.id,io)]);
 assert.equal(r.state,"INSERTED");assert.equal(r.attachmentRequired,true);
 assert.equal(state.inserted,1);assert.equal(state.pasted,1);assert.equal(state.clicked,0);
 const payload=JSON.parse(state.text);assert.equal(payload.omninode_response,true);assert.equal(payload.completed_action,"screenshot");
 await ledger.send(r.id,io);assert.equal(state.clicked,0);
 ledger.observe(r,io);state.now=3000;ledger.observe(r,io);
 assert.equal(r.attachment,"ATTACHMENT_READY_FOR_CONFIRM");
 await ledger.send(r.id,io);assert.equal(state.clicked,0);
 await ledger.confirmAttachment(r.id,io);assert.equal(r.attachment,"ATTACHMENT_VERIFIED");
 await ledger.send(r.id,io);ledger.observe(r,io);
 assert.equal(r.state,"SENT_CONFIRMED");assert.equal(state.clicked,1);
 await ledger.autoDeliver(r.id,io);await ledger.attach(r.id,io);await ledger.send(r.id,io);
 assert.equal(state.inserted,1);assert.equal(state.pasted,1);assert.equal(state.clicked,1);
});
test("unsupported image paste never falls back to text-only send",async()=>{
 const {state,ledger,io}=fixture({supported:false});const r=ledger.prepare("no-paste-001",image);
 await ledger.autoDeliver(r.id,io);await ledger.send(r.id,io);
 assert.equal(r.attachmentRequired,true);assert.equal(r.attachment,"ATTACHMENT_ASSISTED_REQUIRED");
 assert.equal(state.pasted,0);assert.equal(state.clicked,0);
});
test("duplicate result ids are rejected",()=>{
 const {ledger}=fixture();ledger.prepare("duplicate-001",image);
 assert.throws(()=>ledger.prepare("duplicate-001",image),/DUPLICATE_RESULT/);
});
test("response payload cannot be parsed as a new screenshot command",()=>{
 const response=JSON.stringify({omninode_response:true,completed_action:"screenshot",request_id:"auto-ok-001",status:"ok"});
 assert.throws(()=>parseRequest(response,new Map()),/INVALID_REQUEST/);
});
