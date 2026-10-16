const {test}=require('node:test');
const assert=require('node:assert/strict');
const {OmniDesktopBroker,omniConversation}=require('./desktop_broker.js');
function fixture(){
  const tabs=new Map([[1,{id:1,windowId:7,url:'https://www.perplexity.ai/search/chat',active:true}]]);
  const calls=[];
  const api={runtime:{id:'extension',getURL:p=>'chrome-extension://extension/'+p},action:{setBadgeText:()=>{}},tabs:{get:async id=>{if(!tabs.has(id))throw Error('Missing tab');return tabs.get(id)},create:async data=>{calls.push(data);tabs.set(2,{id:2,...data});return {id:2,...data}},update:async(id,data)=>{calls.push({id,...data})}}};
  const client={session:null,open:async()=>{client.session='session'},stop:()=>{client.session=null},execute:async(action,args)=>{calls.push({action,args});return {ok:true,result:{status:'executed'}}}};
  const broker=new OmniDesktopBroker(api,client);
  const sender={id:'extension',url:api.runtime.getURL('desktop.html')};
  return {broker,api,client,sender,tabs,calls};
}
test('normalizes conversation without query or fragment',()=>assert.equal(omniConversation('https://claude.ai/chat/id?private=1#x'),'https://claude.ai/chat/id'));
for(const url of ['http://claude.ai/chat/id','https://claude.ai.evil/chat','https://evil.test/','https://user@claude.ai/','https://claude.ai:1234/'])test('rejects URL '+url,()=>assert.throws(()=>omniConversation(url)));
test('web page sender cannot open native host',async()=>{const f=fixture();await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},{id:'extension',url:'https://www.perplexity.ai/search/chat',tab:{id:1}}));assert.equal(f.client.session,null)});
test('desktop action rejected before local authorization',async()=>{const f=fixture();await assert.rejects(f.broker.handle({type:'desktop-execute',action:'move',args:{}},f.sender));assert.equal(f.calls.length,0)});
test('open binds selected conversation',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);assert.equal(f.broker.owner.conversation,'https://www.perplexity.ai/search/chat');f.broker.stop()});
test('navigation revokes native session',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);f.broker.changed(1,'https://www.perplexity.ai/search/other');assert.equal(f.client.session,null)});
test('creates helper chat in controller window',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await f.broker.handle({type:'ai-open',provider:'gemini'},f.sender);assert.deepEqual(f.calls[0],{windowId:7,url:'https://gemini.google.com/',active:true});f.broker.stop()});
test('does not open arbitrary URL',async()=>{const f=fixture();await f.broker.handle({type:'ai-open',provider:'https://evil.test'},f.sender));assert.equal(f.calls.length,0);f.broker.stop()});
test('does not focus unrelated tab',async()=>{const f=fixture();await f.broker.handle({type:'desktop-open',tabId:1},f.sender);await assert.rejects(f.broker.handle({type:'ai-focus',tabId:99},f.sender));f.broker.stop()});
test('changed tab during consent is rejected',async()=>{const f=fixture();f.client.open=async()=>{f.client.session='session';f.tabs.get(1).url='https://claude.ai/chat/other'};await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},f.sender));assert.equal(f.client.session,null)});
test('background tab cannot silently become controller',async()=>{const f=fixture();f.tabs.get(1).active=false;await assert.rejects(f.broker.handle({type:'desktop-open',tabId:1},f.sender));assert.equal(f.client.session,null)});
