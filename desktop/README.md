# OmniNode desktop primitives

Experimental library, NOT an operational chat-to-desktop bridge.

No listener, autostart, shell endpoint, installer, or privilege elevation. Importing this module does not capture the screen or inject input. Native dependencies are separate from the gateway. Use only in a dedicated local virtualenv, never install them globally for the gateway.

After explicit local consent, a trusted local coordinator may create DesktopSession(windows_backend(), conversation_id). The credential belongs only in trusted local contexts. This library does not verify browser origins, provide a consent window, or authorize arbitrary web callers. Do not expose it over HTTP or wire it into the existing bridge before authentication, consent UI, request lifecycle, and stop handling are implemented.

Actions: screenshot, move, click, scroll, press, hotkey, type, drag. Screenshots are returned as PNG bytes in memory and are not written to disk. Mouse bounds are the primary display only. Keyboard text is printable ASCII only; Unicode is explicitly rejected pending a native Windows backend. No clipboard modification.

Sessions expire (default 10 minutes, maximum 15), bind to a conversation identifier, validate credentials, and can be stopped. Stop prevents subsequent primitives; it cannot undo an input event already delivered to the OS. PyAutoGUI corner fail-safe remains enabled. Key/button cleanup is attempted in finally; OS and backend failures can still prevent release and require further hardening. No crash/retry guarantee exists for input actions: never automatically retry a timed-out click or keystroke.

Executed in assistant environment: 15 unit tests passed with fake input/screenshot backend. No native Windows input, real screenshot, or chat transport was tested. CI unit tests on Windows/Linux are not a live desktop demonstration. Missing: visible local consent/stop UI, Unicode and multi-monitor support, Go integration, authenticated browser transport, screenshot return into this conversation, and real desktop E2E evidence. Existing MQTT TLS/ACL and workspace policies are unchanged.
