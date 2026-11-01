"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const {DeliveryLedger}=require("./text_delivery.js");
const {parseRequest}=require("./content.js");
const image={mime:"image/png",width:1280,height:720,bytes:1024,data_url:"data:image/png;base64,QUJD"};
function ledger(options={}){
  return new DeliveryLedger(options.isActive??(()=>true),options.authorize??(async()=>true),options.records??new Map(),options.clock??Date.now);
}
function io(options={}){
  const state={text:options.initialText??"",sent:false,inserted:0,clicked:0};
  const editor={id:"composer"};
  return {state,editor,
    inspect(){
      if(options.changeAfterInsert&&state.inserted)return {editor:{id:"other"},scope:{},text:"bozza utente",hasText:true,attachments:false,uploading:false,sendButton:null,sendEnabled:false};
      return {editor,state:{},scope:{},text:state.text,hasText:state.text.length>0,attachments:false,uploading:false,sendButton:{},sendEnabled:options.sendEnabled??true};
    },
    canPaste(){return false;},makeFile(){return {};},uploadBaseline(){return new Set();},pasteFile(){},
    insert(_,text){state.text=text;state.inserted++;},
    clickSend(){state.sent=true;state.clicked++;},
    baseline(){return {queries:new Set(),models:new Set()};},
    evidence(){return {composerEmpty:!state.text,outgoingExact:state.sent,generationObserved:state.sent,outgoingAttachment:true};}
  };
}
test("auto delivery preserves an existing user draft",async()=>{
  const l=ledger(),channel=io({initialText:"bozza utente"}),r=await l.autoDeliver("draft-hold-001",channel);
  assert.equal(r.state,"DRAFT_PROTECTED_HOLD");
  assert.equal(channel.state.inserted,0);assert.equal(channel.state.clicked,0);
});
test("auto delivery aborts when the user modifies the composer concurrently",async()=>{
  const l=ledger(),channel=io({changeAfterInsert:true}),r=await l.autoDeliver("race-hold-001",channel);
  assert.equal(r.state,"DRAFT_PROTECTED_HOLD");
  assert.equal(channel.state.clicked,0);
});
test("auto delivery aborts a stale session",async()=>{
  const l=ledger({isActive:()=>false}),channel=io(),r=await l.autoDeliver("stale-001",channel);
  assert.equal(r.state,"ABORTED_SESSION_CHANGE");
  assert.equal(channel.state.inserted,0);assert.equal(channel.state.clicked,0);
});
test("authorized auto delivery inserts and sends exactly once",async()=>{
  const l=ledger(),channel=io(),r=await l.autoDeliver("auto-ok-001",channel);
  l.observe(r,channel);
  assert.equal(r.state,"SENT_CONFIRMED");
  assert.equal(channel.state.inserted,1);assert.equal(channel.state.clicked,1);
  assert.match(channel.state.text,/"omninode_response":true/);
  assert.match(channel.state.text,/"completed_action":"screenshot"/);
  const again=await l.autoDeliver("auto-ok-001",channel);
  assert.equal(again,r);
  assert.equal(channel.state.inserted,1);assert.equal(channel.state.clicked,1);
});
test("duplicate result ids are rejected",()=>{
  const l=ledger(),channel=io();
  l.prepare("duplicate-001",image);
  assert.throws(()=>l.prepare("duplicate-001",image),/DUPLICATE_RESULT/);
});
test("response payload cannot be parsed as a new screenshot command",()=>{
  const response=JSON.stringify({omninode_response:true,completed_action:"screenshot",request_id:"auto-ok-001",status:"ok"});
  assert.throws(()=>parseRequest(response,new Map()),/INVALID_REQUEST/);
});
