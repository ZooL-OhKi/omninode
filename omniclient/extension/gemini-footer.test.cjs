const {test}=require("node:test"),a=require("node:assert/strict");
const {footerCompletion,LiveBirthGate}=require("./content.js");
const selectors=["thumb-up-button button","thumb-down-button button","regenerate-button button","copy-button button"];
function fixture(){
 const node={textContent:"new",querySelectorAll:s=>s==="message-actions"?bars:[]};
 const bar={closest:s=>s==="model-response"?node:null,querySelectorAll:s=>s==="button"?buttons:(groups[s]||[])};
 const buttons=selectors.map(()=>({disabled:false,hidden:false,code:false,getAttribute:()=>null,getClientRects(){return this.hidden?[]:[{}];},closest(s){if(s==="message-actions")return bar;if(s==="pre, code-block")return this.code?{}:null;return null;}}));
 const groups=Object.fromEntries(selectors.map((s,i)=>[s,[buttons[i]]]));let bars=[bar];
 return {node,bar,buttons,groups,setBars:x=>bars=x};
}
test("observed message-actions quartet is complete",()=>a.equal(footerCompletion(fixture().node).complete,true));
for(const selector of selectors)test("requires "+selector,()=>{const f=fixture();f.groups[selector]=[];a.equal(footerCompletion(f.node).complete,false);});
test("code-block copy does not complete footer",()=>{const f=fixture();f.buttons[3].code=true;a.equal(footerCompletion(f.node).complete,false);});
test("copy alone never suffices",()=>{const f=fixture();for(const s of selectors.slice(0,3))f.groups[s]=[];a.equal(footerCompletion(f.node).complete,false);});
for(const field of ["disabled","hidden"])test("unavailable button "+field,()=>{const f=fixture();f.buttons[0][field]=true;a.equal(footerCompletion(f.node).complete,false);});
test("ambiguous footer rejected",()=>{const f=fixture();f.setBars([f.bar,f.bar]);a.equal(footerCompletion(f.node).complete,false);});
test("duplicate required control rejected",()=>{const f=fixture();f.groups[selectors[0]].push(f.buttons[0]);a.equal(footerCompletion(f.node).complete,false);});
test("no footer fails closed",()=>{const f=fixture();f.setBars([]);a.equal(footerCompletion(f.node).complete,false);});
test("null attributes: footer quiescence is required after Stop",()=>{
 const f=fixture(),g=new LiveBirthGate([],0);g.added([f.node],f.node,1);g.mutation(f.node);
 const signal=()=>{const x=footerCompletion(f.node);return {text:"json",controls:x.signature,complete:x.complete,valid:true,blockCount:1,streaming:false,ariaBusy:null,dataIsStreaming:null};};
 a.equal(g.sample(f.node,{...signal(),streaming:true},10000),"OBSERVING_MUTATIONS");
 a.equal(g.sample(f.node,signal(),11000),"COMPLETION_BAR_READY");
 a.equal(g.sample(f.node,signal(),13999),"COMPLETION_BAR_READY");
 a.equal(g.sample(f.node,signal(),14000),"SETTLED");
 f.buttons[0].disabled=true;a.equal(g.sample(f.node,signal(),15000),"OBSERVING_MUTATIONS");
 f.buttons[0].disabled=false;a.equal(g.sample(f.node,signal(),16000),"COMPLETION_BAR_READY");
 a.equal(g.sample(f.node,signal(),18999),"COMPLETION_BAR_READY");
 a.equal(g.sample(f.node,signal(),19000),"SETTLED");
});
