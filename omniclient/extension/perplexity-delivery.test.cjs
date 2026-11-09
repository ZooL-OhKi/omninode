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
