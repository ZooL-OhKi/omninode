"use strict";
class OmniNativeClient {
  constructor(runtime, timeout = 20000) {
    this.runtime = runtime;
    this.timeout = timeout;
    this.port = null;
    this.pending = null;
    this.session = null;
    this.sequence = 0;
  }
  stop(reason = "Desktop disconnected; input is not retried") {
    const port = this.port;
    this.port = null;
    this.session = null;
    if (this.pending) {
      const pending = this.pending;
      this.pending = null;
      clearTimeout(pending.timer);
      pending.reject(new Error(reason));
    }
    if (port) { try { port.disconnect(); } catch {} }
  }
  _message(message) {
    const pending = this.pending;
    if (!pending) { this.stop("Unsolicited native message"); return; }
    if (!message || message.ok !== true) {
      this.stop(message?.error || "Native operation failed; do not retry input"); return;
    }
    if (pending.kind === "open") {
      if (typeof message.session_id !== "string" || !/^[A-Za-z0-9_-]{16,128}$/.test(message.session_id) || message.next_sequence !== 0) {
        this.stop("Invalid native handshake"); return;
      }
      this.session = message.session_id;
      this.sequence = 0;
    } else if (message.session_id !== this.session || message.sequence !== pending.sequence) {
      this.stop("Native result correlation mismatch"); return;
    }
    clearTimeout(pending.timer);
    this.pending = null;
    pending.resolve(message);
  }
  _request(payload, kind, timeout) {
    if (this.pending) return Promise.reject(new Error("Desktop operation already in progress"));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => this.stop("Native timeout; session closed; do not retry input"), timeout);
      this.pending = {resolve, reject, timer, kind, sequence: payload.sequence};
      try { this.port.postMessage(payload); }
      catch { this.stop("Native transport failed; do not retry input"); }
    });
  }
  async open(conversation) {
    if (this.port) throw new Error("Native session already open");
    if (typeof conversation !== "string" || !conversation || conversation.length > 1024) throw new Error("Invalid conversation binding");
    const port = this.runtime.connectNative("com.omninode.desktop");
    this.port = port;
    port.onMessage.addListener(message => { if (this.port === port) this._message(message); });
    port.onDisconnect.addListener(() => {
      const diagnostic = this.runtime.lastError?.message;
      if (this.port === port) this.stop(diagnostic || "Native host disconnected");
    });
    return this._request({type: "open", conversation}, "open", 120000);
  }
  execute(action, args) {
    if (!this.port || !this.session) return Promise.reject(new Error("Desktop session is not authorized"));
    if (this.pending) return Promise.reject(new Error("Desktop operation already in progress"));
    const sequence = this.sequence++;
    return this._request({session_id: this.session, sequence, action, args}, "action", this.timeout);
  }
}
if (typeof module !== "undefined" && module.exports) module.exports = {OmniNativeClient};
else globalThis.OmniNativeClient = OmniNativeClient;
