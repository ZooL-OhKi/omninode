const {test}=require('node:test');
const assert=require('node:assert/strict');
const {OmniNativeClient}=require('./native_client.js');
function fixture(timeout=1000) {
  const sent=[]; const listeners={};
  const port={onMessage:{addListener:f=>listeners.message=f},onDisconnect:{addListener:f=>listeners.disconnect=f},postMessage:m=>sent.push(m),disconnect:()=>{port.closed=true;listeners.disconnect?.()}};
  const runtime={connectNative:name=>{assert.equal(name,'com.omninode.desktop');return port}};
  return {client:new OmniNativeClient(runtime,timeout),sent,port,reply:m=>listeners.message(m)};
}
async function opened(timeout) {
  const f=fixture(timeout);const pending=f.client.open('authorized conversation');
  f.reply({ok:true,session_id:'session_0123456789abcdef',next_sequence:0});await pending;return f;
}
test('opening requires native local authorization handshake',async()=>{const f=fixture();const p=f.client.open('chat');assert.deepEqual(f.sent,[{type:'open',conversation:'chat'}]);f.reply({ok:true,session_id:'session_0123456789abcdef',next_sequence:0});await p;f.client.stop()});
test('cannot execute before authorization',async()=>{const f=fixture();await assert.rejects(f.client.execute('move',{}));assert.equal(f.sent.length,0)});
test('correlates result and increments sequence',async()=>{const f=await opened();const p=f.client.execute('move',{x:2,y:3});assert.equal(f.sent[1].sequence,0);f.reply({ok:true,session_id:f.client.session,sequence:0,result:{status:'executed'}});await p;const next=f.client.execute('press',{key:'enter'});assert.equal(f.sent[2].sequence,1);f.reply({ok:true,session_id:f.client.session,sequence:1,result:{}});await next;f.client.stop()});
test('rejects concurrent actions without sending them',async()=>{const f=await opened();const p=f.client.execute('move',{});await assert.rejects(f.client.execute('click',{}));assert.equal(f.sent.length,2);f.reply({ok:true,session_id:f.client.session,sequence:0,result:{}});await p;f.client.stop()});
test('wrong result sequence disconnects',async()=>{const f=await opened();const p=f.client.execute('move',{});f.reply({ok:true,session_id:f.client.session,sequence:8,result:{}});await assert.rejects(p);assert.equal(f.port.closed,true)});
test('wrong result session disconnects',async()=>{const f=await opened();const p=f.client.execute('move',{});f.reply({ok:true,session_id:'another',sequence:0,result:{}});await assert.rejects(p);assert.equal(f.port.closed,true)});
test('timeout closes channel with no retry',async()=>{const f=await opened(10);await assert.rejects(f.client.execute('click',{}));assert.equal(f.sent.length,2);assert.equal(f.port.closed,true)});
test('stop rejects pending work',async()=>{const f=await opened();const p=f.client.execute('move',{});f.client.stop();await assert.rejects(p);assert.equal(f.client.session,null)});
test('denied native consent closes channel',async()=>{const f=fixture();const p=f.client.open('chat');f.reply({ok:false,error:'local consent denied'});await assert.rejects(p);assert.equal(f.port.closed,true)});
