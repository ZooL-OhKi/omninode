'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {imageBaseline,previewCandidates}=require('./perplexity_delivery.js');
const img=(src,changes={})=>({src,currentSrc:src,isConnected:true,complete:true,naturalWidth:1280,naturalHeight:720,getClientRects:()=>[{}],closest:()=>null,...changes});
test('fresh portal preview outside composer is found',()=>{
 const old=img('old'),fresh=img('blob:new');let nodes=[old];
 const doc={querySelectorAll:()=>nodes};const baseline=imageBaseline(doc);nodes=[old,fresh];
 assert.deepEqual(previewCandidates(doc,baseline),[fresh]);
});
test('historic image rerender with same source is excluded',()=>{
 const baseline=new Set(['old']);
 assert.deepEqual(previewCandidates({querySelectorAll:()=>[img('old')]},baseline),[]);
});
test('reused node with new source becomes a candidate',()=>{
 const node=img('old'),doc={querySelectorAll:()=>[node]};const baseline=imageBaseline(doc);node.src=node.currentSrc='blob:new';
 assert.deepEqual(previewCandidates(doc,baseline),[node]);
});
test('unloaded, hidden, conversation and disconnected images excluded',()=>{
 const nodes=[img('a',{complete:false}),img('b',{getClientRects:()=>[]}),img('c',{closest:()=>({})}),img('d',{isConnected:false}),img('e',{naturalWidth:0})];
 assert.deepEqual(previewCandidates({querySelectorAll:()=>nodes},new Set()),[]);
});
test('multiple candidates remain ambiguous',()=>{
 const nodes=[img('a'),img('b')];assert.equal(previewCandidates({querySelectorAll:()=>nodes},new Set()).length,2);
});
