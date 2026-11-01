const {test}=require("node:test"),a=require("node:assert/strict");
const {LiveBirthGate,OneShotGate}=require("./content.js");
const signal={text:"json",controls:"copy|feedback",complete:true,streaming:false,valid:true,blockCount:1};
function fixture(){const n={textContent:"new"},g=new LiveBirthGate([{textContent:"old"}],100);g.added([n],n,101);g.mutation(n);return {n,g};}
test("null attributes require completion bar and >=3000ms",()=>{const {n,g}=fixture();a.equal(g.sample(n,{...signal,ariaBusy:null,dataIsStreaming:null},200),"COMPLETION_BAR_READY");a.equal(g.sample(n,signal,3199),"COMPLETION_BAR_READY");a.equal(g.sample(n,signal,3200),"SETTLED");});
test("long pause without controls never settles",()=>{const {n,g}=fixture();for(const ms of [200,5000,10000])a.equal(g.sample(n,{...signal,complete:false},ms),"OBSERVING_MUTATIONS");});
for(const c of [{streaming:true},{complete:false},{text:"changed"},{controls:"different"}])test("reset "+JSON.stringify(c),()=>{const {n,g}=fixture();g.sample(n,signal,200);a.equal(g.sample(n,{...signal,...c},4000),"OBSERVING_MUTATIONS");});
test("multiple blocks rejected",()=>{const {n,g}=fixture();a.equal(g.sample(n,{...signal,blockCount:2},200),"REJECTED_MULTI_BLOCK");});
test("baseline rerender ignored",()=>{const n={textContent:" old "},g=new LiveBirthGate([{textContent:"old"}],100);g.added([n],n,200);g.mutation(n);a.equal(g.sample(n,signal,9000),"BASELINE_IGNORED");});
test("batch and non-last history ignored",()=>{const x={textContent:"x"},y={textContent:"y"},g=new LiveBirthGate([],100);g.added([x,y],y,200);g.mutation(y);a.equal(g.sample(y,signal,9000),"BASELINE_IGNORED");const z={textContent:"z"};g.added([z],y,300);g.mutation(z);a.equal(g.sample(z,signal,9000),"BASELINE_IGNORED");});
test("no live text mutation means no completion",()=>{const n={textContent:"x"},g=new LiveBirthGate([],100);g.added([n],n,200);g.mutation(n,false);a.equal(g.sample(n,signal,9000),"OBSERVING_MUTATIONS");});
test("one-shot turn binding and explicit confirmation",()=>{const g=new OneShotGate(),x={},y={};a.equal(g.allow(x,"r"),false);g.arm(x);a.equal(g.allow(y,"r"),false);a.equal(g.allow(x,"r"),true);a.equal(g.allow(x,"r",true),false);a.equal(g.allow(y,"s"),false);a.equal(g.allow(y,"s",true),true);});
