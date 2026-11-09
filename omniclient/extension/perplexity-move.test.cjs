'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const policy=require('./action_policy.js');
const {omniParseCommand,omniBuildResultMessage}=require('./perplexity_adapter.js');
const {makeResultText}=require('./perplexity_delivery.js');
const command={request_id:'omni-move-0001',action:'move',args:{x:400,y:200,observation_id:'omni-screen-0001',coord_space:'image_pixels'}};
const image={kind:'image',width:1280,height:720,source_width:1920,source_height:1080,data_url:'data:image/jpeg;base64,AAAA',completed_action:'move',observation_id:command.request_id,observed_at_ms:1000,observation_ttl_ms:60000,coord_space:'image_pixels'};
test('move parses only with a reference and image coordinate space',()=>{
 assert.deepEqual(omniParseCommand(JSON.stringify(command),policy),command);
 for(const args of [{...command.args,observation_id:''},{...command.args,coord_space:'win32_pixels'},{...command.args,x:1280},{...command.args,y:-1},{...command.args,x:1.5},{...command.args,extra:true}])assert.equal(omniParseCommand(JSON.stringify({...command,args}),policy),null);
 const args={...command.args};delete args.observation_id;assert.equal(omniParseCommand(JSON.stringify({...command,args}),policy),null);
});
test('click and typing remain unavailable in this vertical',()=>{
 for(const action of ['click','type','notepad_write','hotkey'])assert.equal(omniParseCommand(JSON.stringify({...command,action}),policy),null);
});
test('action result requires matching execution and observation reference',()=>{
 const response={ok:true,request_id:command.request_id,completed_action:'move',result:image,action_result:{status:'executed',reference_id:command.args.observation_id}};
 assert.match(omniBuildResultMessage(command,response),/move/);
 assert.throws(()=>omniBuildResultMessage(command,{...response,action_result:{status:'executed',reference_id:'wrong-id'}}),/INVALID_ACTION_RESULT/);
 assert.throws(()=>omniBuildResultMessage(command,{...response,completed_action:'screenshot'}),/INVALID_ACTION_RESULT/);
});
test('delivery preserves metadata, actual action and excludes image bytes',()=>{
 const result=JSON.parse(makeResultText(image,command.request_id));
 assert.equal(result.completed_action,'move');assert.equal(result.execution_status,'executed');
 assert.equal(result.observation_id,command.request_id);assert.equal(result.source_width,1920);
 assert.equal(result.data_url,undefined);assert.equal(result.data_base64,undefined);
 assert.throws(()=>makeResultText({...image,observation_id:'wrong-id'},command.request_id),/INVALID_OBSERVATION_METADATA/);
 assert.throws(()=>makeResultText({...image,source_width:1},command.request_id),/INVALID_OBSERVATION_GEOMETRY/);
 const screenshot=JSON.parse(makeResultText({...image,completed_action:'screenshot'},command.request_id));assert.equal(screenshot.execution_status,'observed');
});
