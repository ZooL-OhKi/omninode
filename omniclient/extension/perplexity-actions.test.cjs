'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const policy=require('./action_policy.js');
const {omniParseCommand,omniBuildResultMessage}=require('./perplexity_adapter.js');
const {makeResultText}=require('./perplexity_delivery.js');
const cases={click:{x:400,y:200,button:'left'},type:{text:'OmniNode'},press:{key:'enter'},hotkey:{keys:['ctrl','a']}};
for(const [action,args] of Object.entries(cases)){
 test(action+' requires exact schema and fresh observation reference',()=>{
  const command={request_id:'bounded-action-001',action,args:{...args,observation_id:'bounded-observe-001',coord_space:'image_pixels'}};
  assert.deepEqual(omniParseCommand(JSON.stringify(command),policy),command);
  for(const bad of [{...command.args,extra:true},{...args},{...command.args,observation_id:''},{...command.args,coord_space:'win32_pixels'}])assert.equal(omniParseCommand(JSON.stringify({...command,args:bad}),policy),null);
  const image={kind:'image',mime:'image/jpeg',width:1280,height:720,source_width:3840,source_height:2160,data_url:'data:image/jpeg;base64,AAAA',completed_action:action,observation_id:command.request_id,observed_at_ms:1000,observation_ttl_ms:60000,coord_space:'image_pixels'};
  const response={ok:true,request_id:command.request_id,completed_action:action,result:image,action_result:{status:'executed',reference_id:command.args.observation_id}};
  assert.match(omniBuildResultMessage(command,response),new RegExp(action));
  for(const bad of [{...response,completed_action:'screenshot'},{...response,action_result:{status:'executed',reference_id:'wrong-reference'}},{...response,result:{...image,completed_action:'screenshot'}},{...response,action_result:{status:'observed',reference_id:command.args.observation_id}}])assert.throws(()=>omniBuildResultMessage(command,bad),/INVALID_ACTION_RESULT/);
  const text=JSON.parse(makeResultText(image,command.request_id));
  assert.equal(text.execution_status,'executed');assert.equal(text.completed_action,action);assert.equal(text.data_url,undefined);
 });
}
