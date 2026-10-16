# Native desktop channel

Implemented: length-prefixed JSON over stdin/stdout, strict JSON decoding, 128 KiB incoming and 1 MiB outgoing frame limits, per-process session identifier, monotonic sequence consumed before effect, no automatic retry, Windows binary pipe mode, extension-origin check, local Tk consent and visible STOP. The desktop credential never leaves the host. No network listener is opened.

Native host startup expects the browser-supplied extension origin as argv[1] and an identical trusted OMNINODE_NATIVE_ORIGIN configured by a future installer. It refuses to start without a matching chrome-extension origin. Opening a host channel requires a first message with type=open and conversation, followed by explicit local approval. Actions require session_id, sequence, action, args. Closing the channel revokes the session. STOP revokes input but cannot undo already delivered events; disconnect detection during a blocking OS call is not immediate.

Executed in assistant environment: Python compilation and 14 native protocol/dispatch tests passed with mock desktop session. The existing 15 primitive tests are separate; CI now discovers both suites. Tk consent, Windows binary pipes, native extension launch and physical desktop control were NOT exercised here.

Not installed, registered, connected to the extension, or available from the current web chat. No installer or browser-side native port is included in this patch. Native screenshots larger than the frame limit are rejected and stop the session; resizing/chunking remains to implement. Full chat-to-desktop and multi-AI coordination remain incomplete. Existing Go workspace bridge and MQTT security are unchanged.
