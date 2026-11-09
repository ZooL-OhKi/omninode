'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const delivery=require('./perplexity_delivery.js');
test('image accept list uses full tokens',()=>{
 for(const accept of ['image/*','.png','.txt,.json,.png','image/png'])assert.equal(delivery.accepts({accept},'image/png'),true);
 assert.equal(delivery.accepts({accept:'.pngx'},'image/png'),false);
 assert.equal(delivery.accepts({accept:'.txt'},'image/png'),false);
 assert.equal(delivery.accepts({accept:'.jpeg'},'image/jpeg'),true);
});
test('inactive sessions never touch document',async()=>{
 let touched=false;const doc={querySelectorAll(){touched=true;throw Error('unexpected');}};
 await assert.rejects(delivery.deliver({isActive:()=>false},doc),/DELIVERY_SESSION_CHANGED/);
 assert.equal(touched,false);
});
test('ambiguous editors stop before upload',async()=>{
 const editor={isConnected:true,getClientRects:()=>[{}]};
 await assert.rejects(delivery.deliver({isActive:()=>true},{querySelectorAll:()=>[editor,editor]}),/COMPOSER_AMBIGUOUS/);
});
function fixture(command){
 const f={calls:0,ticks:0,live:true,listeners:new Map(),selected:false};
 f.editor={textContent:'',isConnected:true,focus(){},addEventListener(k,v){f.listeners.set(k,v);},removeEventListener(k){f.listeners.delete(k);}};
 f.doc={createRange:()=>({selectNodeContents(e){assert.equal(e,f.editor);},collapse(v){assert.equal(v,false);}}),defaultView:{getSelection:()=>({removeAllRanges(){},addRange(){f.selected=true;}})},execCommand(...args){f.calls++;assert.equal(f.selected,true);return command(f,...args);}};
 f.wait=async()=>{f.ticks++;if(f.onTick)f.onTick();};
 f.run=()=>delivery.insertVerified(f.editor,'payload',()=>f.live,f.doc,{wait:f.wait});
 return f;
}
test('false command return with actual inserted text is verified once',async()=>{
 const f=fixture(x=>{x.editor.textContent='payload';return false;});
 assert.equal((await f.run()).state,'INSERT_VERIFIED');assert.equal(f.calls,1);assert.equal(f.listeners.size,0);
});
test('delayed insertion waits without repeating command',async()=>{
 const f=fixture(()=>true);f.onTick=()=>{if(f.ticks===4)f.editor.textContent='payload';};
 await f.run();assert.equal(f.calls,1);assert.ok(f.ticks>=6);
});
test('existing draft is never overwritten',async()=>{
 const f=fixture(()=>true);f.editor.textContent='user draft';
 await assert.rejects(f.run(),/DRAFT_PROTECTED_HOLD/);assert.equal(f.calls,0);
});
test('different inserted text stops and is not retried',async()=>{
 const f=fixture(x=>{x.editor.textContent='different';return true;});
 await assert.rejects(f.run(),/INSERT_TEXT_MISMATCH/);assert.equal(f.calls,1);
});
test('session expiry stops verification',async()=>{
 const f=fixture(()=>true);f.onTick=()=>{f.live=false;};
 await assert.rejects(f.run(),/INSERT_SESSION_CHANGED/);assert.equal(f.calls,1);assert.equal(f.listeners.size,0);
});
test('editor replacement stops verification',async()=>{
 const f=fixture(()=>true);f.onTick=()=>{f.editor.isConnected=false;};
 await assert.rejects(f.run(),/INSERT_EDITOR_REPLACED/);assert.equal(f.calls,1);
});
test('rejected command has bounded wait and no retry',async()=>{
 const f=fixture(()=>false);await assert.rejects(f.run(),/INSERT_COMMAND_REJECTED/);
 assert.equal(f.calls,1);assert.equal(f.ticks,30);
});
test('trusted user input aborts even when text happens to match',async()=>{
 const f=fixture(x=>{x.editor.textContent='payload';return true;});
 f.onTick=()=>f.listeners.get('beforeinput')?.({isTrusted:true});
 await assert.rejects(f.run(),/DRAFT_CHANGED/);assert.equal(f.calls,1);
});
