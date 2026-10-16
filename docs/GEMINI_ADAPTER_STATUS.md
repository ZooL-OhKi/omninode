# Gemini adapter correction

Status: experimental; not certified operational.

Changes: read rendered pre/code within new model-response elements instead of literal Markdown fences across document.body; ignore pre-activation elements; bind to conversation URL; visible errors; preserve nonempty drafts; stop and session limits; correlated result insertion and conditional automatic send.

Execution requires explicit aria-busy=false or data-is-streaming=false on model-response. These attributes are fixture assumptions, NOT verified against the user's live Gemini DOM. Missing completion evidence blocks execution. A stable text interval alone never authorizes execution. Quoted examples inside new assistant replies remain an unresolved protocol-authenticity risk: do not certify this adapter for unattended use.

Executed in assistant environment: Node parser/delivery unit tests 16 passed; Chromium synthetic DOM checks 7 passed (history, streaming, unknown completion, rendered JSON, draft preservation, conditional send, stop). Bridge was mocked. No real Gemini login, live local filesystem effect, or native extension service-worker integration was tested.

Core issues still open: concurrent and crash-safe payload idempotency, removal of third in-memory registry, loopback listener enforcement, caller sessions and revocation, metadata protection, actual extension Origin validation. No merge, deploy, or Windows update performed by this patch.
