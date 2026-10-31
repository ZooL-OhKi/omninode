const {test}=require('node:test');
const assert=require('node:assert/strict');
const {OmniDesktopBroker,omniConversation}=require('./desktop_broker.js');
function fixture(){
  const tabs=new Map([[1,{id:1,windowId:7,url:'https://gemini.google.com/app/chat',active:true}]]);
  const calls=[];
  const sent=[];
  const api={runtime:{id:'extension',getURL:p=>'chrome-extension://extension/'+p},action:{setBadgeText:()=>{}},tabs:{get:async id=>{if(!tabs.has(id))throw Error('Missing tab');return tabs.get(id)},create:async data=>{calls.push(data);tabs.set(2,{id:2,...data});return {id:2,...data}},update:async(id,data)=>{calls.push({id,...data})},sendMessage:async(tabId,message)=>{sent.push({tabId,message});return {ok:true}}}};
  const client={session:null,open:async()=>{client.session='session'},stop:()=>{client.session=null},execute:async(action,args)=>{calls.push({action,args});return {ok:true,kind:'image',width:1280,height:800,bytes:1000,data_url:'data:image/png;base64,x'}}};
  const broker=new OmniDesktopBroker(api,client,{tokenFactory:()=>'a'.repeat(64)});
  const sender={id:'extension',url:api.runtime.getURL('desktop.html')};
  const bridgeSender={id:'extension',url:'https://gemini.google.com/app/chat',tab:{id:1}};
  return {broker,api,client,sender,bridgeSender,tabs,calls,sent};
}
function bridgeRequest(overrides={}){
  return {type:'ai-bridge-request',activation_id:'a'.repeat(64),request_id:'req-12345678',issued_at:Date.now(),stream_state:'settled',payload:{action:'screenshot',args:{}},...overrides};
}
test('normalizes conversation without query or fragment',()=>assert.equal(omniConversation('https://claude.ai/chat/id?private=1#x'),'https://claude.ai/chat/id'));
for(const url of ['http://claude.ai/chat/id','https://claude.ai.evil/chat','https://evil.test/','https://user@claude.ai/','https://claude.ai:1234/'])test('rejects URL '+url,()=>assert.throws(()=>omniConversation(url)));
test('web page sender cannot open native host',async()=>{const f=fixture();await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},{id:'extension',url:'https://gemini.google.com/app/chat',tab:{id:1}}));assert.equal(f.client.session,null)});
test('desktop action rejected before local authorization',async()=>{const f=fixture();await assert.rejects(f.broker.handle({type:'desktop-execute',action:'move',args:{}},f.sender));assert.equal(f.calls.length,0)});
test('open binds selected conversation and sends activation only to its tab',async()=>{const f=fixture();const result=await f.broker.handle({type:'desktop-open',tabId:1},f.sender);assert.equal(f.broker.owner.conversation,'https://gemini.google.com/app/chat');assert.equal(f.sent.length,1);assert.equal(f.sent[0].tabId,1);assert.equal(f.sent[0].message.activation_id,'a'.repeat(64));assert.equal(result.expires_at,f.broker.activation.expiresAt);f.broker.stop()});
test('navigation revokes native session',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);f.broker.changed(1,'https://gemini.google.com/app/other');assert.equal(f.client.session,null)});
test('authorized bridge request executes once and correlates result',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);const result=await f.broker.handle(bridgeRequest(),f.bridgeSender);assert.equal(result.request_id,'req-12345678');assert.equal(result.result.kind,'image');assert.deepEqual(f.calls.at(-1),{action:'screenshot',args:{}});f.broker.stop()});
test('bridge request from another tab is rejected',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await assert.rejects(f.broker.handle(bridgeRequest(),{...f.bridgeSender,tab:{id:99}}));assert.equal(f.calls.length,0);f.broker.stop()});
test('bridge request with invalid activation token is rejected',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await assert.rejects(f.broker.handle(bridgeRequest({activation_id:'b'.repeat(64)}),f.bridgeSender));assert.equal(f.calls.length,0);f.broker.stop()});
test('streaming response cannot trigger desktop execution',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await assert.rejects(f.broker.handle(bridgeRequest({stream_state:'streaming'}),f.bridgeSender));assert.equal(f.calls.length,0);f.broker.stop()});
test('duplicate request_id is never re-executed',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await f.broker.handle(bridgeRequest(),f.bridgeSender);await assert.rejects(f.broker.handle(bridgeRequest(),f.bridgeSender));assert.equal(f.calls.filter(call=>call.action).length,1);f.broker.stop()});
test('expired activation stops the session',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);f.broker.activation.expiresAt=Date.now()-1;await assert.rejects(f.broker.handle(bridgeRequest(),f.bridgeSender));assert.equal(f.client.session,null)});
test('unknown action is rejected',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await assert.rejects(f.broker.handle(bridgeRequest({payload:{action:'shell',args:{}}}),f.bridgeSender));assert.equal(f.calls.length,0);f.broker.stop()});
test('changed tab during consent is rejected',async()=>{const f=fixture();f.client.open=async()=>{f.client.session='session';f.tabs.get(1).url='https://claude.ai/chat/other'};await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},f.sender));assert.equal(f.client.session,null)});
test('background tab cannot silently become controller',async()=>{const f=fixture();f.tabs.get(1).active=false;await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},f.sender));assert.equal(f.client.session,null)});
