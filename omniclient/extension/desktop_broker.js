"use strict";
const OMNI_AI_SITES = Object.freeze({gemini:"https://gemini.google.com/", claude:"https://claude.ai/", perplexity:"https://www.perplexity.ai/"});
const REQUEST_ID = /^[A-Za-z0-9._-]{8,128}$/;
const ALLOWED_ACTIONS = Object.freeze(["screenshot"]);

function omniConversation(raw) {
  const url = new URL(raw);
  if (url.protocol !== "https:" || url.username || url.password || url.port || !["gemini.google.com","claude.ai","perplexity.ai","www.perplexity.ai"].includes(url.hostname)) throw new Error("Select an authorized AI web chat tab");
  return url.origin + url.pathname;
}

class OmniDesktopBroker {
  constructor(api, client, options = {}) {
    this.api = api;
    this.client = client;
    this.owner = null;
    this.epoch = 0;
    this.helpers = new Set();
    this.activationTtl = options.activationTtl ?? 600000;
    this.requestTtl = options.requestTtl ?? 30000;
    this.maxRequests = options.maxRequests ?? 20;
    this.tokenFactory = options.tokenFactory ?? (() => {
      const bytes = new Uint8Array(32);
      globalThis.crypto.getRandomValues(bytes);
      return Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
    });
    this.activation = null;
    this.requests = new Map();
  }

  trusted(sender) {
    return sender?.id === this.api.runtime.id && sender.url === this.api.runtime.getURL("desktop.html") && !sender.tab;
  }

  stop() {
    this.epoch++;
    this.owner = null;
    this.helpers.clear();
    this.activation = null;
    this.requests.clear();
    this.client.stop();
    this.api.action.setBadgeText({text:""});
  }

  changed(tabId, url) {
    if (this.owner?.tabId !== tabId) return;
    try { if (omniConversation(url) === this.owner.conversation) return; } catch {}
    this.stop();
  }

  _assertActiveBridge(sender, message) {
    if (!this.owner || !this.client.session || !this.activation) throw new Error("No authorized desktop session");
    if (Date.now() > this.activation.expiresAt) { this.stop(); throw new Error("Authorized session expired"); }
    if (sender?.tab?.id !== this.owner.tabId) throw new Error("Request is not from the authorized conversation tab");
    if (message?.activation_id !== this.activation.token) throw new Error("Invalid bridge activation token");
    return this.activation;
  }

  async _assertCurrentConversation() {
    const current = await this.api.tabs.get(this.owner.tabId);
    if (omniConversation(current.url) !== this.owner.conversation) { this.stop(); throw new Error("Controller conversation changed"); }
    return current;
  }

  async handle(message, sender) {
    if (!this.trusted(sender)) throw new Error("Untrusted desktop caller");
    if (message.type === "desktop-stop") { this.stop(); return {ok:true}; }
    if (message.type === "desktop-status") return {ok:true, active:Boolean(this.owner && this.client.session), conversation:this.owner?.conversation || null};

    if (message.type === "desktop-open") {
      if (this.owner) throw new Error("Stop the existing session first");
      if (!Number.isInteger(message.tabId)) throw new Error("Invalid selected tab");
      const epoch = this.epoch;
      const tab = await this.api.tabs.get(message.tabId);
      if (epoch !== this.epoch) throw new Error("Activation cancelled");
      if (!tab.active) throw new Error("Select the controller tab before activation");
      const conversation = omniConversation(tab.url);
      this.owner = {tabId:tab.id, windowId:tab.windowId, conversation};
      try {
        await this.client.open(conversation);
        const current = await this.api.tabs.get(tab.id);
        if (epoch !== this.epoch || omniConversation(current.url) !== conversation) throw new Error("Conversation changed during consent");
        const issuedAt = Date.now();
        const expiresAt = issuedAt + this.activationTtl;
        const activationId = this.tokenFactory();
        this.activation = {token:activationId, issuedAt, expiresAt};
        await this.api.tabs.sendMessage(tab.id, {type:"omninode-activation", activation_id:activationId, conversation, expires_at:expiresAt});
        if (epoch !== this.epoch) throw new Error("Activation cancelled");
        this.api.action.setBadgeText({text:"ON"});
        return {ok:true, conversation, expires_at:expiresAt};
      } catch (error) { this.stop(); throw error; }
    }

    if (message.type === "ai-bridge-request") {
      const activation = this._assertActiveBridge(sender, message);
      await this._assertCurrentConversation();
      if (typeof message.request_id !== "string" || !REQUEST_ID.test(message.request_id)) throw new Error("Invalid request_id");
      if (this.requests.has(message.request_id)) throw new Error("Duplicate request_id; request not re-executed");
      if (this.requests.size >= this.maxRequests) { this.stop(); throw new Error("Request limit reached; session stopped"); }
      if (!Number.isSafeInteger(message.issued_at) || message.issued_at < activation.issuedAt - 1000 || message.issued_at > Date.now() + 5000) throw new Error("Invalid request timestamp");
      if (message.stream_state !== "settled") throw new Error("Response is not settled; refusing request");
      const payload = message.payload;
      if (!payload || Array.isArray(payload) || typeof payload !== "object") throw new Error("Invalid bridge payload");
      if (Object.keys(payload).sort().join(",") !== "action,args") throw new Error("Invalid bridge payload schema");
      if (typeof payload.action !== "string" || !ALLOWED_ACTIONS.includes(payload.action)) throw new Error("Unsupported desktop action");
      if (!payload.args || Array.isArray(payload.args) || typeof payload.args !== "object") throw new Error("Invalid action arguments");

      const requestId = message.request_id;
      const expiresAt = Date.now() + this.requestTtl;
      this.requests.set(requestId, {status:"pending", expiresAt});
      try {
        const result = await this.client.execute(payload.action, payload.args);
        this.requests.set(requestId, {status:"completed", expiresAt, result});
        return {ok:true, request_id:requestId, result};
      } catch (error) {
        this.requests.set(requestId, {status:"failed", expiresAt, error:String(error?.message || error)});
        throw error;
      }
    }

    if (!this.owner || !this.client.session) throw new Error("No authorized desktop session");
    await this._assertCurrentConversation();
    if (message.type === "desktop-execute") return this.client.execute(message.action, message.args);
    if (message.type === "ai-open") {
      if (!Object.hasOwn(OMNI_AI_SITES, message.provider)) throw new Error("Unsupported AI provider");
      const tab = await this.api.tabs.create({windowId:this.owner.windowId, url:OMNI_AI_SITES[message.provider], active:true});
      this.helpers.add(tab.id);
      return {ok:true, tabId:tab.id};
    }
    if (message.type === "ai-focus") {
      if (message.tabId !== this.owner.tabId && !this.helpers.has(message.tabId)) throw new Error("Tab not owned by this session");
      await this.api.tabs.update(message.tabId, {active:true});
      return {ok:true};
    }
    throw new Error("Unsupported desktop message");
  }
}

if (typeof module !== "undefined" && module.exports) module.exports = {OmniDesktopBroker, omniConversation};
else globalThis.OmniDesktopBroker = OmniDesktopBroker;
