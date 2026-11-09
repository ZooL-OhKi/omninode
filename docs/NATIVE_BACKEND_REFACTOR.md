# Native backend refactor: stato e limiti

Aggiornamento: 9 novembre 2026. Questo documento descrive responsabilità, meccanismi di sicurezza e limiti del backend nativo. Non certifica input fisico o produzione.

## Responsabilità

`desktop_control.py` gestisce concessioni, schemi esatti, scadenza, STOP, lock e deadline cooperativa di 12 secondi per `execute()`.

`windows_input_backend.py` gestisce piani deterministici, esecuzione input e chiamate Win32. Le import pubbliche `DesktopSession` e `windows_backend` restano disponibili.

L’host richiede DPI awareness per monitor prima di creare finestre Tk e rifiuta modalità incompatible. L’installer valida le dipendenze sorgente e rifiuta percorsi collegati.

## Target e focus

Un click o drag confermato seleziona un target root HWND e PID. Il broker richiede un target confermato anche per `type`, `press` e `hotkey`.

Il backend richiede il ripristino ordinario del focus Windows e verifica l’identità in foreground; abortisce se Windows rifiuta o il focus cambia. I controlli geometrici non provano pixel, controlli o stato applicazione invariati.

Nessun titolo target, testo digitato o credenziale viene aggiunto ai log.

## Cleanup e typing

Il cleanup tenta il rilascio di tasti/pulsanti tramite `SendInput`, senza disabilitare `FAILSAFE` di PyAutoGUI. Ogni rilascio tracciato viene tentato anche se un altro fallisce.

I rilasci restano best effort: input già consegnato al sistema operativo non può essere annullato. Il typing pianifica 12 ms per carattere, fino a 256 caratteri; non è una garanzia di performance reale.

La deadline di 12 secondi è cooperativa e non può interrompere una cattura o scrittura OS bloccante. Il timeout JS di 20 secondi è per richiesta nativa, non una deadline end-to-end.

Nessun jitter casuale, overshoot, spoofing biometrico o bypass CAPTCHA è incluso.

## Validazione e rollback

Prima della pubblicazione erano stati eseguiti 30 test Python: 15 nuovi planner/mock/installer e 15 legacy desktop. Non erano state rivendicate input fisico Windows, API DPI, `SendInput` o nuova CI.

Il rollback deve ripristinare l’intero commit in modo coerente e riavviare l’host nativo. Un revert Git da solo non aggiorna un processo Windows in esecuzione. Verificare percorsi installati e modifiche locali prima di ogni deploy.
