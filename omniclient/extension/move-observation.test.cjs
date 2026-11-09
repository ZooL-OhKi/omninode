'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {OmniMoveBroker,requireObservation,validateMovePayload,OBSERVATION_TTL_MS}=require('./move_broker.js');
const image={kind:'image',width:1280,height:720,source_width:1920,source_height:1080};
const args={x:10,y:20,observation_id:'obs-test-0001',coord_space:'image_pixels'};
test('valid reference resolves the recorded observation',()=>{
 const observation={id:args.observation_id,image,at:1000};
 assert.equal(requireObservation({observation},args,1001),observation);
});
test('missing and wrong observations are rejected',()=>{
 assert.throws(()=>requireObservation({},args,1001),/OBSERVATION_REFERENCE_REQUIRED/);
 assert.throws(()=>requireObservation({observation:{id:'another-id',at:1000}},args,1001),/OBSERVATION_REFERENCE_REQUIRED/);
});
test('expiry boundary and clock reversal fail closed',()=>{
 const s={observation:{id:args.observation_id,image,at:1000}};
 assert.throws(()=>requireObservation(s,args,1000+OBSERVATION_TTL_MS),/STALE_OBSERVATION_REJECTED/);
 assert.throws(()=>requireObservation(s,args,999),/STALE_OBSERVATION_REJECTED/);
 assert.throws(()=>requireObservation(s,{...args,coord_space:'win32_pixels'},1001),/INVALID_COORD_SPACE/);
});
test('unknown actions and unknown fields are rejected',()=>{
 assert.throws(()=>validateMovePayload('arbitrary',{}),/INVALID_ACTION/);
 assert.throws(()=>validateMovePayload('move',{...args,extra:true}),/INVALID_ACTION_SCHEMA/);
 assert.doesNotThrow(()=>validateMovePayload('move',args));
});
test('invalid button, drag endpoint, scroll and key schemas are rejected',()=>{
 assert.throws(()=>validateMovePayload('click',{x:1,y:2,button:'invalid'}));
 assert.throws(()=>validateMovePayload('drag',{x:1,y:2,to_x:-1,to_y:2}));
 assert.throws(()=>validateMovePayload('scroll',{steps:21}));
 assert.throws(()=>validateMovePayload('press',{key:''}));
 assert.throws(()=>validateMovePayload('hotkey',{keys:[]}));
});
test('recorded image receives metadata without retaining mutable geometry',()=>{
 const broker=new OmniMoveBroker({},{});broker.isCurrent=()=>true;
 const s={},result={...image};broker.recordObservation(s,'obs-test-0001',result);
 assert.equal(result.observation_id,'obs-test-0001');
 assert.equal(result.coord_space,'image_pixels');
 assert.equal(result.observation_ttl_ms,OBSERVATION_TTL_MS);
 result.width=1;assert.equal(s.observation.image.width,1280);
});
test('inactive session cannot record an observation',()=>{
 const broker=new OmniMoveBroker({},{});broker.isCurrent=()=>false;
 const s={};broker.recordObservation(s,'obs-test-0001',{...image});assert.equal(s.observation,undefined);
});
