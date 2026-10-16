const {test} = require('node:test');
const assert = require('node:assert/strict');
const {parseRequest,canDeliver} = require('./content.js');
const valid = {request_id:'request-0001',path:'gemini/new.md',content:'Hello'};
test('rendered code without markdown fences is parsed',()=>assert.deepEqual(parseRequest(JSON.stringify(valid)),valid));
test('rejects unknown command field',()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,command:'sh'}))));
test('rejects incomplete streamed JSON',()=>assert.throws(()=>parseRequest('{"request_id":')));
for (const path of ['../escape','/tmp/out','.omninode/tasks','a/.OMNINODE/x','C:\\out','a/../out','a//out']) {
  test('rejects unsafe path '+path,()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,path}))));
}
test('rejects oversized content',()=>assert.throws(()=>parseRequest(JSON.stringify({...valid,content:'x'.repeat(524289)}))));
test('allows empty composer in active conversation',()=>assert.equal(canDeliver(true,true,false,''),true));
test('preserves existing draft even if unfocused',()=>assert.equal(canDeliver(true,true,false,'my draft'),false));
test('stop prohibits insertion',()=>assert.equal(canDeliver(false,true,false,''),false));
test('navigation prohibits insertion',()=>assert.equal(canDeliver(true,false,false,''),false));
test('streaming prohibits insertion',()=>assert.equal(canDeliver(true,true,true,''),false));
