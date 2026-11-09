'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const p=require('./action_policy.js');
test('unknown and inherited action names fail closed',()=>{
 for(const action of ['shell','constructor','toString','__proto__'])a.throws(()=>p.validate(action,{}));
});
test('screenshot accepts only an empty object',()=>{
 p.validate('screenshot',{});
 for(const args of [{x:1},{share_result:true},{reference_id:'screen-0001'},[],null])a.throws(()=>p.validate('screenshot',args));
});
test('move preserves observation-bound image coordinates',()=>{
 p.validate('move',{x:100,y:200,observation_id:'screen-0001',coord_space:'image_pixels'});
 for(const extra of [{x:1280},{y:800},{x:-1},{y:1.5},{observation_id:'bad'},{coord_space:'win32_pixels'},{shell:'cmd'}])a.throws(()=>p.validate('move',{x:100,y:200,observation_id:'screen-0001',coord_space:'image_pixels',...extra}));
});
test('text, buttons, key and scroll constraints are enforced',()=>{
 p.validate('type',{text:'caffè'});
 a.throws(()=>p.validate('type',{text:'line\nnext'}));
 a.throws(()=>p.validate('click',{x:1,y:2,button:'unknown'}));
 a.throws(()=>p.validate('drag',{x:1,y:2,to_x:1280,to_y:3}));
 a.throws(()=>p.validate('hotkey',{keys:[]}));
 a.throws(()=>p.validate('press',{key:'\n'}));
 a.throws(()=>p.validate('scroll',{steps:21}));
});
