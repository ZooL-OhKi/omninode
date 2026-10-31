const {test}=require('node:test');
const assert=require('node:assert/strict');
const {parseRequest,canDeliver,isSettled}=require('./content.js');
const valid='{"action":"screenshot","args":{},"request_id":"req-12345678"}';
test('parses one authorized screenshot request',()=>{
  const request=parseRequest(valid);
  assert.equal(request.action,'screenshot');
  assert.equal(request.request_id,'req-12345678');
});
for(const text of [
  '{"content":"x","path":"a.txt","request_id":"req-12345678"}',
  '{"action":"shell","args":{},"request_id":"req-12345678"}',
  '{"action":"screenshot","args":{"cmd":"dir"},"request_id":"req-12345678"}',
  '{"action":"screenshot","args":{},"request_id":"short"}',
  'not-json'
])test('rejects malformed or unauthorized request: '+text,()=>assert.throws(()=>parseRequest(text)));
test('does not deliver into a non-empty user draft',()=>{
  assert.equal(canDeliver(true,true,false,'bozza utente'),false);
  assert.equal(canDeliver(true,true,false,''),true);
});
test('does not deliver while streaming or after navigation',()=>{
  assert.equal(canDeliver(true,true,true,''),false);
  assert.equal(canDeliver(true,false,false,''),false);
  assert.equal(canDeliver(false,true,false,''),false);
});
test('requires explicit completion and quiescence',()=>{
  const response={getAttribute:()=>null,closest:()=>null};
  assert.equal(isSettled(response,4000),false);
  const complete={getAttribute:name=>name==='aria-busy'?'false':null,closest:()=>null};
  assert.equal(isSettled(complete,1000),false);
  assert.equal(isSettled(complete,3000),true);
});
