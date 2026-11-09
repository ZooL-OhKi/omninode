'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const api=require('./perplexity_adapter.js');
const policy=require('./action_policy.js');
const command={request_id:'omni-test-0002',action:'screenshot',args:{}};
test('raw rendered JSON and fenced JSON',()=>{
 assert.deepEqual(api.omniParseCommand(JSON.stringify(command),policy),command);
 assert.deepEqual(api.omniParseCommand('```json\n'+JSON.stringify(command)+'\n```',policy),command);
});
test('reject ambiguity, extra fields and unsupported actions',()=>{
 for(const value of [{...command,action:'click'},{...command,args:{x:1}},{...command,extra:true},{...command,request_id:'short'}])assert.equal(api.omniParseCommand(JSON.stringify(value),policy),null);
 assert.equal(api.omniParseCommand('prefix '+JSON.stringify(command),policy),null);
 assert.equal(api.omniParseCommand(JSON.stringify(command)+JSON.stringify(command),policy),null);
});
test('extract a single rendered code block, not surrounding prose',()=>{
 const code={textContent:JSON.stringify(command)};
 const pre={closest:()=>null,querySelector:()=>code};
 const p={querySelector:()=>({querySelectorAll:()=>[pre]})};
 assert.equal(api.omniExtractResponseText(p),JSON.stringify(command));
 assert.equal(api.omniExtractResponseText({querySelector:()=>({querySelectorAll:()=>[pre,pre]})}), '');
});
test('result uses normalized image and checks request correlation',()=>{
 const r={ok:true,request_id:command.request_id,result:{kind:'image',width:800,height:600,data_url:'data:image/png;base64,AAAA'}};
 assert.match(api.omniBuildResultMessage(command,r),/800x600/);
 assert.throws(()=>api.omniBuildResultMessage(command,{...r,request_id:'wrong'}));
 assert.throws(()=>api.omniBuildResultMessage(command,{...r,result:{}}));
});
