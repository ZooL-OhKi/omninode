const {test}=require("node:test"),a=require("node:assert/strict"),p=require("./action_policy.js");
const args={reference_id:"screen-0001",share_result:true,text:"caffè",x:200,y:200};
test("bounded task requires exact schema and explicit result sharing",()=>{p.validate("notepad_write",args);for(const extra of [{share_result:false},{share_result:undefined},{text:"x".repeat(257)},{x:1280},{text:"hello\nworld"},{shell:"cmd"}])a.throws(()=>p.validate("notepad_write",{...args,...extra}));});
test("task sharing flag is rejected on ordinary actions",()=>{a.throws(()=>p.validate("click",{reference_id:"screen-0001",x:2,y:2,button:"left",share_result:true}));p.validate("screenshot",{});});
