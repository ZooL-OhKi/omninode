"use strict";
const {test}=require("node:test"),a=require("node:assert/strict");
const {OmniDesktopBroker}=require("./desktop_broker.js");
function fixture(){
 const tab={id:1,windowId:7,active:true,url:"https://gemini.google.com/app/chat"};let calls=0;
 const api={runtime:{id:"extension",getURL:p=>"chrome-extension://extension/"+p},action:{setBadgeText:()=>{}},tabs:{get:async()=>({...tab}),sendMessage:async()=>({ok:true})}};
 const client={session:null,open:async()=>{calls++;client.session="native";},stop:()=>{client.session=null;}};
 const broker=new OmniDesktopBroker(api,client,{tokenFactory:()=>"a".repeat(64)});
 return {broker,tab,get calls(){return calls;},sender:{id:"extension",frameId:0,tab:{id:1},url:tab.url}};
}
test("same-tab top-frame automatic opening remains available",async()=>{
 const f=fixture();try{a.equal((await f.broker.handle({type:"desktop-open"},f.sender)).ok,true);a.equal(f.calls,1);}finally{f.broker.stop();}
});
test("content script cannot select an explicit tab",async()=>{
 const f=fixture();await a.rejects(f.broker.handle({type:"desktop-open",tabId:1},f.sender));a.equal(f.calls,0);
});
test("subframe automatic opening is rejected",async()=>{
 const f=fixture();await a.rejects(f.broker.handle({type:"desktop-open"},{...f.sender,frameId:1}));a.equal(f.calls,0);
});
test("automatic opener URL must match actual tab before native opening",async()=>{
 const f=fixture();await a.rejects(f.broker.handle({type:"desktop-open"},{...f.sender,url:"https://gemini.google.com/app/other"}));a.equal(f.calls,0);
});
test("inactive automatic opener is rejected",async()=>{
 const f=fixture();f.tab.active=false;await a.rejects(f.broker.handle({type:"desktop-open"},f.sender));a.equal(f.calls,0);
});
