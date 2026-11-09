const {test}=require("node:test"),a=require("node:assert/strict");
const {createBridgeListener}=require("./service_worker.js");
function run(handle,normalize=x=>x){let stops=0;const broker={handle,isCurrent:()=>true,stop:()=>stops++};return {broker,listener:createBridgeListener(broker,normalize),stops:()=>stops};}
function reply(f){return new Promise(r=>f.listener({type:"ai-bridge-request",request_id:"request-0001",activation_id:"token"},{},r));}
test("rejection does not stop",async()=>{const f=run(async()=>{throw {rejected:true,code:"NON_TOP_FRAME"};});a.equal((await reply(f)).rejected,true);a.equal(f.stops(),0);});
test("stale sends no application payload",async()=>{const f=run(async()=>({stale_dropped:true}));a.equal(await reply(f),undefined);});
test("bad image closes authorized session",async()=>{const f=run(async()=>({activation_id:"token",_session:{}}),()=>{throw Error();});a.equal((await reply(f)).code,"INVALID_NATIVE_IMAGE");a.equal(f.stops(),1);});
test("success preserves correlation",async()=>{const f=run(async()=>({activation_id:"token",request_id:"request-0001",result:{image:true},_session:{}}));const r=await reply(f);a.equal(r.activation_id,"token");a.equal(r.request_id,"request-0001");a.deepEqual(r.result,{image:true,completed_action:"screenshot",auto_delivery:true});});
test("observation metadata reaches the correlated result",async()=>{
 const session={};const f=run(async()=>({activation_id:"token",request_id:"request-0001",result:{image:true},_session:session}));
 let calls=0;f.broker.recordObservation=(s,id,image)=>{calls++;a.equal(s,session);a.equal(id,"request-0001");image.observation_id=id;};
 const r=await reply(f);a.equal(calls,1);a.equal(r.result.observation_id,r.request_id);a.equal(r.result.auto_delivery,true);
});
test("actual action and acknowledgement remain correlated",async()=>{
 const actionResult={status:"executed",reference_id:"screen-0001"};
 const f=run(async()=>({activation_id:"token",request_id:"request-0001",result:{image:true},_session:{},completed_action:"move",action_result:actionResult}));
 const r=await reply(f);a.equal(r.completed_action,"move");a.equal(r.result.completed_action,"move");a.deepEqual(r.action_result,actionResult);
});
test("observation recording failure stops the session",async()=>{
 const f=run(async()=>({activation_id:"token",request_id:"request-0001",result:{image:true},_session:{}}));
 f.broker.recordObservation=()=>{throw Error("invalid geometry");};
 const r=await reply(f);a.equal(r.ok,false);a.equal(r.code,"INVALID_NATIVE_IMAGE");a.equal(f.stops(),1);a.equal(r.result,undefined);
});
