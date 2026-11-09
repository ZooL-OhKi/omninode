"use strict";
const OMNI_AI_SITES=Object.freeze({gemini:"https://gemini.google.com/",claude:"https://claude.ai/",perplexity:"https://www.perplexity.ai/"});
class BridgeRejectedError extends Error {constructor(code){super(code);this.code=code;this.rejected=true;}}
class BridgeFatalError extends Error {constructor(code){super(code);this.code=code;this.fatal=true;}}
function omniConversation(raw){const u=new URL(raw);if(u.protocol!=="https:"||u.username||u.password||u.port||!["gemini.google.com","claude.ai","perplexity.ai","www.perplexity.ai"].includes(u.hostname))throw new BridgeRejectedError("INVALID_CONVERSATION");return u.origin+u.pathname;}
class OmniDesktopBroker {
  constructor(api,client,options={}){
    this.api=api;this.client=client;this.owner=null;this.session=null;this.activation=null;this.epoch=0;this.opening=false;this.helpers=new Set();this.requests=new Map();
    this.activationTtl=options.activationTtl??86400000;this.maxRequests=options.maxRequests??500;
    this.tokenFactory=options.tokenFactory??(()=>{const b=new Uint8Array(32);globalThis.crypto.getRandomValues(b);return Array.from(b,x=>x.toString(16).padStart(2,"0")).join("");});
  }
  trusted(s){return s?.id===this.api.runtime.id;}
  stop(){this.epoch++;if(this.session){this.session.state="STOPPED";clearTimeout(this.session.timer);}this.session=null;this.owner=null;this.activation=null;this.opening=false;this.requests=new Map();this.helpers.clear();this.client.stop("Desktop session stopped; input is not retried");this.api.action.setBadgeText({text:""});}
  changed(id,url){if(this.owner?.tabId!==id)return;try{if(omniConversation(url)===this.owner.conversation)return;}catch{}this.stop();}
  isCurrent(s){if(!s||this.session!==s||s.epoch!==this.epoch||s.state!=="ACTIVE")return false;if(Date.now()>=s.expiresAt||this.client.session!==s.nativeSession){this.stop();return false;}return true;}
  _assertActiveBridge(sender,m,bind=false){
    if(sender?.id!==this.api.runtime.id)throw new BridgeRejectedError("WRONG_EXTENSION");
    if(sender.frameId!==0)throw new BridgeRejectedError("NON_TOP_FRAME");
    const s=this.session;
    if(!s||sender.tab?.id!==s.tabId)throw new BridgeRejectedError("WRONG_TAB");
    let url;try{url=omniConversation(sender.url);}catch{throw new BridgeRejectedError("WRONG_URL");}
    if(url!==s.conversation)throw new BridgeRejectedError("WRONG_URL");
    if(m.activation_id!==s.activationId)throw new BridgeRejectedError("INVALID_ACTIVATION");
    if(!this.isCurrent(s))throw new BridgeRejectedError("SESSION_INACTIVE");
    if(s.documentId!==null&&sender.documentId!==s.documentId)throw new BridgeRejectedError("WRONG_DOCUMENT");
    if(!bind&&!s.bound)throw new BridgeRejectedError("DOCUMENT_NOT_BOUND");
    if(!bind&&m.stream_state!=="settled")throw new BridgeRejectedError("NOT_SETTLED");
    if(!bind&&s.inFlightRequestId!==null)throw new BridgeRejectedError("BRIDGE_BUSY");
    return s;
  }
  async bridge(m,sender){
    const s=this._assertActiveBridge(sender,m,m.type==="bridge-bind");
    if(m.type==="bridge-bind"){if(!s.bound){s.documentId=typeof sender.documentId==="string"?sender.documentId:null;s.bound=true;}return {ok:true,activation_id:s.activationId};}
    if(typeof m.request_id!=="string"||!/^[A-Za-z0-9._-]{8,128}$/.test(m.request_id))throw new BridgeRejectedError("INVALID_REQUEST_ID");
    if(s.requests.has(m.request_id))throw new BridgeRejectedError("DUPLICATE_REQUEST");
    if(s.requests.size>=this.maxRequests)throw new BridgeRejectedError("REQUEST_LIMIT");
    if(!Number.isSafeInteger(m.issued_at)||m.issued_at<s.issuedAt||m.issued_at>Date.now()+5000)throw new BridgeRejectedError("INVALID_TIMESTAMP");
    const p=m.payload;
    if(!p||Object.keys(p).sort().join(",")!=="action,args"||p.action!=="screenshot"||!p.args||Array.isArray(p.args)||typeof p.args!=="object"||Object.keys(p.args).length)throw new BridgeRejectedError("INVALID_PAYLOAD");
    s.inFlightRequestId=m.request_id;s.requests.set(m.request_id,{status:"pending"});
    try{
      const tab=await this.api.tabs.get(s.tabId);
      if(!this.isCurrent(s))return {stale_dropped:true};
      if(omniConversation(tab.url)!==s.conversation){this.stop();return {stale_dropped:true};}
      const result=await this.client.execute(p.action,p.args);
      if(!this.isCurrent(s))return {stale_dropped:true};
      s.requests.set(m.request_id,{status:"completed"});
      return {ok:true,request_id:m.request_id,activation_id:s.activationId,result,_session:s};
    }catch(error){if(this.session!==s||this.epoch!==s.epoch||Date.now()>=s.expiresAt){if(this.session===s)this.stop();return {stale_dropped:true};}this.stop();throw new BridgeFatalError("NATIVE_EXECUTION_FAILED");}
    finally{if(this.session===s)s.inFlightRequestId=null;}
  }
  async handle(m,sender){
    if(m?.type!=="desktop-open")return this._handle(m,sender);
    if(!this.trusted(sender))throw new BridgeRejectedError("UNTRUSTED_POPUP");
    const popup=sender.url===this.api.runtime.getURL("desktop.html")&&!sender.tab;
    if(!popup){
      if(Object.hasOwn(m,"tabId")||sender.frameId!==0||!Number.isInteger(sender.tab?.id))throw new BridgeRejectedError("UNTRUSTED_POPUP");
      omniConversation(sender.url);
    }
    const tabId=Number.isInteger(m.tabId)?m.tabId:sender?.tab?.id;
    if(!Number.isInteger(tabId))throw new BridgeRejectedError("INVALID_TAB");
    const pending=this._pendingOpen;
    if(pending&&pending.epoch===this.epoch){
      if(pending.tabId!==tabId)throw new BridgeRejectedError("OPENING_OTHER_TAB");
      return pending.promise;
    }
    const record={tabId,epoch:this.epoch,promise:null};
    this._pendingOpen=record;
    record.promise=Promise.resolve().then(()=>this._handle({...m,tabId},sender));
    try{
      return await record.promise;
    }finally{
      if(this._pendingOpen===record)this._pendingOpen=null;
    }
  }
  async _handle(m,sender){
    if(["bridge-bind","ai-bridge-request"].includes(m?.type))return this.bridge(m,sender);
    if(!this.trusted(sender))throw new BridgeRejectedError("UNTRUSTED_POPUP");
    if(m.type==="desktop-stop"){this.stop();return {ok:true};}
    if(m.type==="desktop-status")return {ok:true,active:this.isCurrent(this.session),conversation:this.owner?.conversation??null};
    if(m.type==="desktop-open"){
      if(this.opening)throw new BridgeRejectedError("SESSION_ALREADY_OPEN");if(this.owner)this.stop();
      if(!Number.isInteger(m.tabId))m.tabId=sender?.tab?.id;if(!Number.isInteger(m.tabId))throw new BridgeRejectedError("INVALID_TAB");
      this.opening=true;const epoch=this.epoch;
      try{
        const tab=await this.api.tabs.get(m.tabId);
        if(epoch!==this.epoch)throw new BridgeRejectedError("ACTIVATION_CANCELLED");
        
        if(tab.active!==true)throw new BridgeRejectedError("INACTIVE_TAB");
        const conversation=omniConversation(tab.url);
        if(sender.tab&&omniConversation(sender.url)!==conversation)throw new BridgeRejectedError("CONVERSATION_CHANGED");
        this.owner={tabId:tab.id,windowId:tab.windowId,conversation};
        await this.client.open(conversation);
        if(epoch!==this.epoch)throw new BridgeRejectedError("ACTIVATION_CANCELLED");
        const current=await this.api.tabs.get(tab.id);
        if(epoch!==this.epoch)throw new BridgeRejectedError("ACTIVATION_CANCELLED");
        if(omniConversation(current.url)!==conversation||current.active!==true)throw new BridgeRejectedError("CONVERSATION_CHANGED");
        const issuedAt=Date.now(),activationId=this.tokenFactory(),expiresAt=issuedAt+this.activationTtl;
        const s={...this.owner,state:"ACTIVE",epoch,activationId,issuedAt,expiresAt,nativeSession:this.client.session,documentId:null,bound:false,inFlightRequestId:null,requests:new Map()};
        this.session=s;this.requests=s.requests;this.activation={token:activationId,issuedAt,expiresAt};
        s.timer=setTimeout(()=>{if(this.session===s)this.stop();},this.activationTtl);s.timer.unref?.();
        const ack=await this.api.tabs.sendMessage(tab.id,{type:"omninode-activation",activation_id:activationId,conversation,expires_at:expiresAt},{frameId:0});
        if(!this.isCurrent(s)||ack?.ok!==true)throw new BridgeRejectedError("ACTIVATION_CANCELLED");
        this.api.action.setBadgeText({text:"ON"});return {ok:true,conversation,expires_at:expiresAt};
      }catch(error){if(this.epoch===epoch)this.stop();throw error;}
      finally{if(this.epoch===epoch)this.opening=false;}
    }
    const s=this.session;if(!this.isCurrent(s))throw new BridgeRejectedError("SESSION_INACTIVE");
    const current=await this.api.tabs.get(s.tabId);
    if(!this.isCurrent(s))return {stale_dropped:true};
    if(omniConversation(current.url)!==s.conversation){this.stop();return {stale_dropped:true};}
    if(m.type==="desktop-execute"){
      if(s.inFlightRequestId!==null)throw new BridgeRejectedError("BRIDGE_BUSY");s.inFlightRequestId="popup";
      try{const result=await this.client.execute(m.action,m.args);return this.isCurrent(s)?result:{stale_dropped:true};}
      catch(error){if(!this.isCurrent(s))return {stale_dropped:true};this.stop();throw new BridgeFatalError("NATIVE_EXECUTION_FAILED");}
      finally{if(this.session===s)s.inFlightRequestId=null;}
    }
    if(m.type==="ai-open"){
      if(!Object.hasOwn(OMNI_AI_SITES,m.provider))throw new BridgeRejectedError("UNSUPPORTED_PROVIDER");
      const tab=await this.api.tabs.create({windowId:s.windowId,url:OMNI_AI_SITES[m.provider],active:true});
      if(!this.isCurrent(s))return {stale_dropped:true};this.helpers.add(tab.id);return {ok:true,tabId:tab.id};
    }
    if(m.type==="ai-focus"){
      if(m.tabId!==s.tabId&&!this.helpers.has(m.tabId))throw new BridgeRejectedError("UNOWNED_TAB");
      await this.api.tabs.update(m.tabId,{active:true});return this.isCurrent(s)?{ok:true}:{stale_dropped:true};
    }
    throw new BridgeRejectedError("UNSUPPORTED_MESSAGE");
  }
}
if(typeof module!=="undefined"&&module.exports)module.exports={OmniDesktopBroker,omniConversation,BridgeRejectedError,BridgeFatalError};
else Object.assign(globalThis,{OmniDesktopBroker,BridgeRejectedError,BridgeFatalError});
