'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {sendReady}=require('./perplexity_delivery.js');
const ready={fileAssigned:true,previewReady:true,loading:false,alert:false,buttonReady:true};
test('all local readiness conditions required',()=>assert.equal(sendReady(ready),true));
for(const [field,value] of [['fileAssigned',false],['previewReady',false],['loading',true],['alert',true],['buttonReady',false]]){
 test('blocks when '+field+' is unsafe',()=>assert.equal(sendReady({...ready,[field]:value}),false));
}
test('enabled button alone never authorizes send',()=>assert.equal(sendReady({buttonReady:true}),false));
test('missing or nonboolean evidence fails closed',()=>{
 for(const field of Object.keys(ready)){const state={...ready};delete state[field];assert.equal(sendReady(state),false);}
 assert.equal(sendReady({...ready,fileAssigned:'true'}),false);
});
test('Perplexity does not call pixel comparator or duplicate base64 in result text',()=>{
 const src=fs.readFileSync(require.resolve('./perplexity_delivery.js'),'utf8');
 assert.doesNotMatch(src,/comparePixels|image\.data_url/);
 assert.equal((src.match(/send\.click\(\)/g)||[]).length,1);
});
