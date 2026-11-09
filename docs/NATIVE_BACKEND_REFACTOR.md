# Native backend refactor: prepared validation

Base: 607a0c1a7dcc7e9251dc219c95fcf90b57e65d7f.

Two runtime responsibilities: desktop_control.py owns grants, exact action schemas,
session expiry, STOP, locking and a cooperative 12-second deadline per execute().
windows_input_backend.py owns deterministic plans, input execution and Win32 calls.
Public DesktopSession and windows_backend imports remain available.

The host requests per-monitor DPI awareness before creating Tk windows and refuses
an incompatible awareness mode. This requires Windows verification.
The installer validates all required source dependencies and rejects linked paths.

A confirmed click/drag selects a target root HWND and PID. Native keyboard/scroll
requires that target. The backend requests ordinary Windows focus restoration and
verifies foreground identity; it aborts if Windows refuses or focus changes.
Geometry checks alone do not prove unchanged pixels, controls or application state.
No target title, typed text or credentials are added to logs.

Native cleanup attempts key/button release through SendInput, without disabling
PyAutoGUI FAILSAFE. Every tracked release is attempted even if another fails.
Releases remain best effort; already delivered OS input cannot be undone.

Typing plans 12 ms per character, at most 256 characters (3.072 seconds of planned
waits). This is not a wall-clock performance guarantee. The 12-second deadline is
cooperative and cannot preempt a blocking OS capture or write. The existing JS
20-second timeout is per native request, not an end-to-end task deadline.
No random jitter, overshoot, biometric spoofing or CAPTCHA bypass is included.

Validation actually executed before publication: Python sandbox, 30 passing tests:
15 new planner/mock/installer checks plus 15 unchanged legacy desktop tests.
The legacy source blob was verified as 811d4af45ecccfd2b42858021390210f948ec2a8.
No Windows physical input, DPI API, SendInput or new GitHub CI result is claimed.
No deployment, host reinstallation, Oracle change or merge was performed.

Rollback must restore the entire commit coherently and restart the native host;
a Git revert alone does not update a running Windows process. Installed source
paths and local modifications must be checked before any deployment.
