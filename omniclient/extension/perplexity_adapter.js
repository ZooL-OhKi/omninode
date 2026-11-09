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
 if(p.action!=='screenshot'||!policy?.id(p.request_id)||!p.args||Array.isArray(p.args)||typeof p.args!=='object'||Object.keys(p.args).length)return null;
 return p;
}
function omniBuildResultMessage(command,response) {
 const image=response?.result;
 if(response?.ok!==true||response.request_id!==command.request_id||image?.kind!=='image'||!Number.isSafeInteger(image.width)||!Number.isSafeInteger(image.height)||!image.data_url?.startsWith('data:image/'))throw Error('INVALID_IMAGE_RESULT');
 return `OmniNode ${command.request_id}: screenshot acquisito (${image.width}x${image.height}). Immagine non allegata alla chat.`;
}
const api={omniIsCompleted,omniExtractResponseText,omniParseCommand,omniBuildResultMessage};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else Object.assign(globalThis,api);
