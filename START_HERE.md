# Riprendere OmniNode da zero

Aggiornamento: 1 novembre 2026. Leggere [handover corrente](docs/ZERO_CONTEXT_HANDOVER.md), [stato](docs/CURRENT_STATUS.md), [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md).

## Riferimento verificato

Repository ZooL-OhKi/omninode, branch feature/bridge-gemini-vertical. Baseline codice verificata: ee7565746809147cecb1be2dd91990ce127d56f7, estensione 0.3.1. Al controllo GitHub della sessione tutti gli 11 check restituiti per HEAD della PR #9 erano completed/success. PR #9 aperta e non mergiata, base ai-handover-20261015-worker2. Questo aggiornamento documentale produce un commit successivo: verificarne HEAD e CI separatamente.

## Capacita e limiti

Il percorso screenshot -> allegato nella stessa chat Gemini e stato osservato in prove assistite dell'utente. Mouse e tastiera sono collegati nel codice; non dedurne una prova fisica completa.

Il compito notepad_write combina click e testo entro un perimetro Blocco note verificato dal backend. Con share_result:true, un OK locale sul compito autorizza anche il tentativo automatico di inserimento, verifica pixel della preview e invio unico del risultato nella chat corrente. Non e un agente autonomo generale; lo screenshot iniziale resta sul percorso preesistente. Se bozze, allegati o verifica immagine sono incerti, fermarsi senza retry.

L'ultima baseline non e attestata come installata su Windows. I precedenti script di aggiornamento erano fissati a 54d5dda57bba6071bb8caafeb6d52dcb83d82191 e non possono installare automaticamente i commit successivi. Un push GitHub non aggiorna C:, A:, Drive, l'host in esecuzione o Oracle.

## Ordine operativo

1. Verificare strumenti, SHA, diff e CI; distinguere sandbox Python/Node, fixture CI e Windows fisico.
2. Leggere [prossimi passi](NEXT_STEPS.md) e [note del compito](docs/NOTEPAD_TASK_BROWSER.md).
3. Prima di un nuovo aggiornamento locale, verificare percorsi installati, modifiche e backup; preservare [copie e recuperi](RESUME.md).
4. Nessun merge, force push, reset distruttivo, pulizia di stash/branch o deploy implicito.

Usare esecutori disponibili e chiedere solo autorizzazioni specifiche o passi fisici indispensabili. Non inventare lavoro in background, accesso al PC o collaborazione diretta fra IA. Conservare mTLS/ACL, TLS 1.3, OpenRoot/O_EXCL, STOP e protezione delle bozze.
