# Handover del progetto

Per riprendere senza conoscere la chat precedente leggere [handover da zero](docs/ZERO_CONTEXT_HANDOVER.md), [START_HERE](START_HERE.md) e [stato corrente](docs/CURRENT_STATUS.md). Aggiornamento: 1 novembre 2026.

OmniNode estende le chat web esistenti con strumenti autorizzati e controllo desktop; non e un progetto di LLM sostitutivi residenti su Oracle. L'obiettivo comprende schermo, mouse/tastiera, risultati nella stessa conversazione e collaborazione reale con altre IA.

La baseline codice verificata e 9316f6b2eecb252ffe7c7447549bd91a36b91a0f, branch feature/bridge-gemini-vertical, PR #9 aperta all'ultimo controllo, 11 check success. Il commit documentale successivo va verificato separatamente. La prova assistita e2e-image-006 mostra screenshot Windows allegato nella chat Gemini e descrizione visiva del modello. Non prova autonomia, tutte le azioni desktop, resilienza o deploy.

Le priorita sono STOP nativo/browser, race e condizioni ambigue, persistenza/idempotenza, Unicode/DPI/multi-monitor, hardening Go e seconda chat IA. Dettagli e criteri di accettazione in NEXT_STEPS.md. Non rifare il test positivo solo per ricostruire il contesto.

Preservare local-work-20261016-005605, tutti i backup, stash e copie. Allineamento C:/A:/Drive non confermato: il primo script ha fallito il parsing; il file corretto e stato consegnato ma non ha un esito attestato. RESUME.md descrive stati e rischi, inclusa la baseline fissata nello script ora da rivalutare.

Windows, GitHub, Drive e VPS hanno stati separati. Nessun merge, deploy, acquisto o attesa per Copilot e implicito. Le note storiche Phase 2.5 e le vecchie baseline non sono certificazioni correnti: controllare manifest, codice e workflow reali. La storia resta recuperabile da Git. AGENTS.md e SECURITY.md sono normativi.
