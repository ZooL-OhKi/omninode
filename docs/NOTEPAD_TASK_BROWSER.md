# Bounded Notepad task: browser integration

Base: 8a2697d761f6be7af35f199cebf1e864043e1f58.

The extension accepts notepad_write only with reference_id, x, y, text and
share_result:true. Its existing trusted local confirmation displays the action
and exact arguments. That approval authorizes the bounded native click/type task
and automatic sharing of its result/screenshot with the current Gemini chat.
The native Notepad/process, session, STOP and no-retry checks remain required.
Other actions retain their existing per-action confirmations and manual delivery.

The returned task result schedules one insertion, one paste and one send. It
waits for a stable unique preview, compares decoded image pixels to the supplied
screenshot, rechecks authorization/composer/preview, then sends once. Failure to
read pixels (including cross-origin canvas restrictions), changed draft, missing
preview, denied authorization or timeout halts; no automatic fallback or retry.
Pixel comparison is a local UI check, not a provider receipt or model-vision proof.
Preexisting drafts/attachments are not overwritten. A hold requires intervention;
it is not silently resumed. Cancelled records block late authorization effects.

Executed before publication: Node.js sandbox, 12 passing tests (7 mocked-driver,
3 actual-ledger, 2 policy tests), plus syntax checks of five JavaScript modules.
No Chrome DOM, real upload, Win32 input or physical end-to-end task was executed.
GitHub CI on the prospective commit is pending. No deployment or merge performed.

This is one bounded task workflow, NOT a general autonomous agent or an unlimited
delegation to future model commands. Initial screenshot acquisition remains on the
existing path. After a recent screenshot, one approval of notepad_write covers
click, typing and automatic result delivery if all verification gates succeed.
The native files from the preceding tranche must be installed coherently.
