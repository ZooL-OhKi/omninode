# Notepad task: stato della tranche nativa

Aggiornamento: 9 novembre 2026. Questo documento descrive la tranche nativa del task Notepad e i suoi limiti. Non certifica un agente autonomo generale.

## Funzionalità nativa

La sessione nativa accetta `notepad_write` con `x`, `y` e `text`. Esegue un click sinistro e una digitazione sotto lock di sessione e deadline cooperativa, senza conferma intermedia del browser.

Il task verifica un eseguibile Notepad nei percorsi classici Windows o nel percorso protetto `WindowsApps`. Un target root HWND/PID è vincolato per l’intero task. Applicazioni diverse o target cambiati falliscono in modo sicuro prima di ulteriori input.

Il task non invia Enter, non salva, non cancella e non ripete. Inserisce nel punto selezionato; non prova che il documento fosse vuoto o che l’applicazione abbia accettato il testo. L’immagine restituita richiede revisione.

## Policy browser

La policy attuale accetta `notepad_write` con `x`, `y`, `text` e `share_result: true`, oltre a un `observation_id` o `reference_id` valido. Non è un’autorizzazione generale: richiede consenso e riferimenti espliciti.

L’affermazione storica secondo cui la policy rifiutasse `notepad_write` è superata. Non attribuire capacità non verificate al solo fatto che lo schema sia accettato.

## Test e limiti

Sei test unitari con backend mock coprivano ordine dei passi, applicazione rifiutata, testo non valido, STOP, nessun retry e target cambiato. Non esercitavano controlli Win32 reali o input fisico.

La correzione `normcase` per i percorsi classici Windows è una revisione del codice, non una prova di esecuzione Windows. Integrazione completa e CI erano pending alla baseline storica.

Nessun deploy, merge o modifica Oracle è stato eseguito in quella tranche.
