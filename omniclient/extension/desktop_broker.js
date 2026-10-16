"use strict";
const OMNI_AI_SITES = Object.freeze({gemini:"https://gemini.google.com/", claude:"https://claude.ai/", perplexity:"https://www.perplexity.ai/"});
function omniConversation(raw) {
  const url = new URL(raw);
  if (url.protocol !== "https:" || url.username || url.password || url.port || !["gemini.google.com","claude.ai","perplexity.ai","www.perplexity.ai"].includes(url.hostname)) throw new Error("Select an authorized AI web chat tab");
  return url.origin + url.pathname;
}
class OmniDesktopBroker {
  constructor(api, client) { this.api=api; this.client=client; this.owner=null; this.epoch=0; this.helpers=new Set(); }
  trusted(sender) { return sender?.id === this.api.runtime.id && sender.url === this.api.runtime.getURL("desktop.html") && !sender.tab; }
  stop() {
    this.epoch++; this.owner=null; this.helpers.clear(); this.client.stop();
    this.api.action.setBadgeText({text:""});
  }
  changed(tabId, url) {
    if (this.owner?.tabId !== tabId) return;
    try { if (omniConversation(url) === this.owner.conversation) return; } catch {}
    this.stop();
  }
  async handle(message, sender) {
    if (!this.trusted(sender)) throw new Error("Untrusted desktop caller");
    if (message.type === "desktop-stop") { this.stop(); return {ok:true}; }
    if (message.type === "desktop-status") return {ok:true, active:Boolean(this.owner && this.client.session), conversation:this.owner?.conversation || null};
    if (message.type === "desktop-open") {
      if (this.owner) throw new Error("Stop the existing session first");
      if (!Number.isInteger(message.tabId)) throw new Error("Invalid selected tab");
      const epoch=this.epoch;
      const tab=await this.api.tabs.get(message.tabId);
      if (epoch !== this.epoch) throw new Error("Activation cancelled");
      if (!tab.active) throw new Error("Select the controller tab before activation");
      const conversation=omniConversation(tab.url);
      this.owner={tabId:tab.id,windowId:tab.windowId,conversation};
      try {
        await this.client.open(conversation);
        const current=await this.api.tabs.get(tab.id);
        if (epoch !== this.epoch || omniConversation(current.url) !== conversation) throw new Error("Conversation changed during consent");
        this.api.action.setBadgeText({text:"ON"});
        return {ok:true, conversation};
      } catch (error) { this.stop(); throw error; }
    }
    if (!this.owner || !this.client.session) throw new Error("No authorized desktop session");
    const current=await this.api.tabs.get(this.owner.tabId);
    if (omniConversation(current.url) !== this.owner.conversation) { this.stop(); throw new Error("Controller conversation changed"); }
    if (message.type === "desktop-execute") return this.client.execute(message.action,message.args);
    if (message.type === "ai-open") {
      if (!Object.hasOwn(OMNI_AI_SITES,message.provider)) throw new Error("Unsupported AI provider");
      const tab=await this.api.tabs.create({windowId:this.owner.windowId,url:OMNI_AI_SITES[message.provider],active:true});
      this.helpers.add(tab.id);
      return {ok:true,tabId:tab.id};
    }
    if (message.type === "ai-focus") {
      if (message.tabId !== this.owner.tabId && !this.helpers.has(message.tabId)) throw new Error("Tab not owned by this session");
      await this.api.tabs.update(message.tabId,{active:true});
      return {ok:true};
    }
    throw new Error("Unsupported desktop message");
  }
}
if (typeof module !== "undefined" && module.exports) module.exports={OmniDesktopBroker,omniConversation};
else globalThis.OmniDesktopBroker=OmniDesktopBroker;
