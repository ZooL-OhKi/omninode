# Componente desktop sperimentale

[Stato corrente](../docs/CURRENT_STATUS.md). La libreria non e da sola un agente operativo dalla chat.

Sono presenti DesktopSession, backend Windows PyAutoGUI, host Native Messaging con consenso Tk/STOP, installer per utente, preview e client browser. Nessun listener di rete o elevazione automatica. La concessione locale e distinta dal workspace remoto.

Azioni: screenshot, move, click, scroll, press, hotkey, type, drag. Limiti: display principale, testo ASCII stampabile fino a 4096 caratteri, sessione host di 10 minuti; Unicode, multi-monitor e DPI da completare. Fail-safe attivo; stop non annulla eventi gia consegnati e il rilascio dei tasti non e garantito contro ogni guasto.

Non ripetere input dopo un timeout. [Host](NATIVE_STATUS.md), [installer](INSTALL_STATUS.md), [browser](BROWSER_CLIENT_STATUS.md), [immagini](SCREEN_STATUS.md). I test Windows/Linux usano backend simulati; la prova fisica sul PC dell'utente manca.
