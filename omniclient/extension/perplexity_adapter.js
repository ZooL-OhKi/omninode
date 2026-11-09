"use strict";
function omniIsCompleted(p) { return Boolean(p?.querySelector('div[title="Completato"]')); }
function omniExtractResponseText(p) {
 const prose=p?.querySelector('.prose');
 if(!prose)return '';
 const blocks=Array.from(prose.querySelectorAll('pre')).filter(x=>!x.closest('blockquote'));
 if(blocks.length!==1)return '';
 return (blocks[0].querySelector('code')||blocks[0]).textContent.trim();
}
function omniParseCommand(text,policy) {
 if(typeof text!=='string'||text.length>8192)return null;
 const fenced=text.match(/^```json\s*([\s\S]*?)```$/i);
 let p;try{p=JSON.parse(fenced?fenced[1]:text);}catch{return null;}
 if(!p||Array.isArray(p)||Object.keys(p).sort().join(',')!=='action,args,request_id')return null;
 if(!policy?.id(p.request_id)||!p.args||Array.isArray(p.args)||typeof p.args!=='object')return null;
 if(p.action==='screenshot')return Object.keys(p.args).length===0?p:null;
 if(p.action!=='move'||Object.keys(p.args).sort().join(',')!=='coord_space,observation_id,x,y')return null;
 const a=p.args;
 if(!policy.id(a.observation_id)||a.coord_space!=='image_pixels'||!Number.isSafeInteger(a.x)||!Number.isSafeInteger(a.y)||a.x<0||a.y<0||a.x>=1280||a.y>=800)return null;
 try{policy.validate(p.action,a);}catch{return null;}
 return p;
}
function omniBuildResultMessage(command,response) {
 const image=response?.result;
 if(response?.ok!==true||response.request_id!==command.request_id||image?.kind!=='image'||!Number.isSafeInteger(image.width)||!Number.isSafeInteger(image.height)||!image.data_url?.startsWith('data:image/'))throw Error('INVALID_IMAGE_RESULT');
 if(command.action==='move'&&(response.completed_action!=='move'||response.action_result?.status!=='executed'||response.action_result.reference_id!==command.args.observation_id||image.observation_id!==command.request_id))throw Error('INVALID_ACTION_RESULT');
 return `OmniNode ${command.request_id}: ${command.action}; nuova immagine ${image.width}x${image.height}.`;
}
const api={omniIsCompleted,omniExtractResponseText,omniParseCommand,omniBuildResultMessage};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else Object.assign(globalThis,api);
