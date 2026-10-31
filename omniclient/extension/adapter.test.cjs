const {test} = require('node:test');
const assert = require('node:assert/strict');
const {parseRequest,canDeliver,isSettled} = require('./content.js');
const valid = {request_id:'request-0001',action:'screenshot',args:{}};
test('rendered JSON screenshot request is parsed',()=>assert.deepEqual(parseRequest(JSON.stringify(valid)),valid));
test('rejects unknown command field',()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,command:'sh'}))));
test('rejects legacy file-write contract',()=>assert.throws(()=>parseRequest(JSON.stringify({request_id:'request-0001',path:'gemini/new.md',content:'Hello'}))));
test('rejects incomplete streamed JSON',()=>assert.throws(()=>parseRequest('{"request_id":')));
for (const action of ['shell','exec','write','click','type','move']) {
  test('rejects unauthorized action '+action,()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,action}))));
}
for (const args of [null,'x',[1],{command:'dir'}]) {
  test('rejects invalid args '+JSON.stringify(args),()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,args}))));
}
test('rejects invalid request id',()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,request_id:'x'}))));
test('allows empty composer in active conversation',()=>assert.equal(canDeliver(true,true,false,''),true));
test('preserves existing draft even if unfocused',()=>assert.equal(canDeliver(true,true,false,'my draft'),false));
test('stop prohibits insertion',()=>assert.equal(canDeliver(false,true,false,''),false));
test('navigation prohibits insertion',()=>assert.equal(canDeliver(true,false,false,''),false));
test('streaming prohibits insertion',()=>assert.equal(canDeliver(true,true,true,''),false));
test('unsettled response cannot execute',()=>{
  const response={getAttribute:()=>null,closest:()=>null};
  assert.equal(isSettled(response,4000),false);
});
test('response requires explicit completion and quiescence',()=>{
  const response={getAttribute:name=>name==='aria-busy'?'false':null,closest:()=>null};
  assert.equal(isSettled(response,1000),false);
  assert.equal(isSettled(response,3000),true);
});
