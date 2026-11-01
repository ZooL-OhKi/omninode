const {test}=require("node:test"),a=require("node:assert/strict");
const {parseRequest,canDeliver,prepareResultDelivery}=require("./content.js");
const valid={action:"screenshot",args:{},request_id:"request-0001"};
test("strict schema",()=>a.deepEqual(parseRequest(JSON.stringify(valid)),valid));
for(const r of [{...valid,command:"sh"},{...valid,action:"shell"},{...valid,args:{x:1}},{...valid,request_id:"x"},{path:"a",content:"b"}])test("reject "+JSON.stringify(r),()=>a.throws(()=>parseRequest(JSON.stringify(r))));
test("incomplete JSON",()=>a.throws(()=>parseRequest('{"action":')));
test("draft guards",()=>{a.equal(canDeliver(true,true,false,""),true);a.equal(canDeliver(true,true,false,"draft"),false);a.equal(canDeliver(true,true,true,""),false);});
test("prepare never mutates draft",()=>{const e={textContent:"draft"};a.equal(prepareResultDelivery(e,{request_id:"r"}).state,"DRAFT_PROTECTED_HOLD");a.equal(e.textContent,"draft");});
test("attachments and duplicate hold",()=>{const p={request_id:"r",ok:true},seen=new Set();a.equal(prepareResultDelivery({textContent:"",querySelector:()=>({})},p,seen).state,"DRAFT_PROTECTED_HOLD");const e={textContent:" \u200b ",querySelector:()=>null};a.equal(prepareResultDelivery(e,p,seen).state,"READY_FOR_CONTROLLED_INSERTION");a.equal(prepareResultDelivery(e,p,seen).state,"DUPLICATE_RESULT");a.equal(e.textContent," \u200b ");});
