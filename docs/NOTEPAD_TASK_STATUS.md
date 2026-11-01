# Bounded Notepad task: native tranche

Base: 54d5dda57bba6071bb8caafeb6d52dcb83d82191.

The native session accepts notepad_write with exact x/y/text fields. It performs
one left click and one typing operation under the existing session lock and
cooperative operation deadline, without an intermediate browser confirmation.
The task verifies a Windows Notepad executable in the classic Windows paths or
the protected WindowsApps Microsoft.WindowsNotepad package path. A root HWND/PID
pair is bound for the entire task. Other applications and changed targets fail
closed before further input. The task does not send Enter, save, delete or retry.
It inserts at the selected point; it does not prove the document was empty or
that the application accepted the text. The returned image still needs review.

This is NOT a general autonomous agent. The current extension action policy
still rejects notepad_write until the browser tranche is implemented. Automatic
composer upload/verification/send is not implemented by this native tranche.
Existing click/type actions retain their existing confirmation requirements.

Six helper unit tests were executed in the Python sandbox with a mocked backend.
They cover fixed step order, rejected application, invalid text, STOP, no retry
and changed target. They do not exercise Win32 process checks or physical input.
The subsequent normcase correction for classic Windows paths is a code review
fix, not a claim of Windows execution. Full integration and GitHub CI are pending.
No deployment, merge or Oracle change was performed.
