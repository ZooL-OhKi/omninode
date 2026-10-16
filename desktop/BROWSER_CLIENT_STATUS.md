# Browser native client

Implemented native_client.js as an extension-trusted-context library: connectNative(com.omninode.desktop), local approval handshake, one operation at a time, session and sequence correlation, timeout/disconnect revocation and no automatic input retries. The native desktop credential never leaves the Python host. The public channel identifier is not exposed to page DOM by this library.

Executed: 9 Node unit tests passed in assistant environment with a fake Chrome runtime/port. No Chrome native launch or physical desktop action was tested. Existing adapter tests remain separate; CI now runs all extension *.test.cjs files.

This commit deliberately does not add nativeMessaging permission, import the library in the service worker, expose a page message handler, install/register the host, or activate any desktop access. Those require the next integrated extension/installer change with browser sender and conversation binding. The current web chat cannot invoke this library yet. Multi-AI tabs, automatic screenshot attachment, real browser completion detection and unattended coordination remain incomplete. A timeout means effect may be partial or unknown; never retry input automatically.
