# OmniNode: handover per una nuova IA senza contesto

Aggiornamento: 1 novembre 2026, stato della sessione fino alle 03:21 CET. Documento autosufficiente per iniziare l'indagine, non certificazione che il progetto sia finito. Nessun accesso alla vecchia chat e necessario per seguire questo piano.

## 1. Missione e modo di lavorare

L'utente vuole usare IA delle chat web esistenti per osservare e controllare l'ambiente autorizzato con OmniNode, ricevere risultati nella stessa conversazione e proseguire. Schermo, mouse, tastiera e collaborazione con altre IA fanno parte dell'obiettivo. Non sostituire queste IA con un LLM nuovo, non limitare il risultato a un popup e non chiamare autonomia una demo screenshot.

Usare strumenti ed esecutori realmente disponibili per leggere, modificare e testare. Non delegare all'utente prove eseguibili autonomamente; quando non esiste accesso Windows, dirlo e preparare un passo locale preciso. Non inventare terminali, attivita in background, contatti con Gemini o risultati. Ridurre le richieste all'utente alle autorizzazioni e ai passi fisici indispensabili, senza eliminare i gate obbligatori.

## 2. Repository e punto di partenza

- Repository: ZooL-OhKi/omninode, https://github.com/ZooL-OhKi/omninode.
- Branch di lavoro: feature/bridge-gemini-vertical.
- PR #9: aperta all'ultimo controllo, base ai-handover-20261015-worker2. Nessun merge richiesto da questo handover.
- Baseline codice/CI: 9316f6b2eecb252ffe7c7447549bd91a36b91a0f, 11 check success. Il commit che introduce questo documento e successivo; verificarne SHA e CI, non attribuirgli in anticipo i risultati della baseline.
- Base handover storica: 86fe9f2ab8805cd850bf60811de10fb813012cd5; vecchia baseline b669ec4 non e HEAD corrente.

Con un clone gia presente, ispezionare branch, HEAD, status, diff, origin, stash e branch di recupero prima di modificare. Su un ambiente nuovo, clonare il branch di lavoro in una directory nuova fuori dalla sincronizzazione Drive. Non riutilizzare una cartella esistente alla cieca. Con soli strumenti GitHub leggere tramite connettore e non fingere una shell locale.

Ordine di lettura: questo documento, CURRENT_STATUS.md, ../AGENTS.md, ../SECURITY.md, ../RESUME.md, ../BUILD.md, REPOSITORY_MAP.md, ../NEXT_STEPS.md, poi codice e workflow interessati. I documenti storici che dicono ancora chat non dimostrata sono superati, limitatamente alla prova screenshot sotto. Le regole di sicurezza restano valide.

## 3. Architettura da distinguere

- omniclient/: worker Go, MQTT, registro MCP, bridge/UI HTTP, workspace e idempotenza. La presenza di metodi MCP non prova che main avvii uno specifico trasporto.
- omniclient/extension/: manifest, service worker, client/broker nativi, percorso chat e test. Controllare i file effettivamente caricati dal manifest; non assumere che il legacy content.js sia attivo.
- desktop/: primitive Windows, consenso locale, host Native Messaging, framing, installer e screenshot. Leggere README.md, INSTALL_STATUS.md, NATIVE_STATUS.md e CI_NATIVE_DIAG.md come guide da confrontare col codice.
- node1-gateway/: gateway Python, task, policy, audit e MQTT.
- .github/workflows/: definizioni reali dei test. deploy/ e scripts/ non descrivono lo stato live dei servizi.

UI/bridge HTTP Go e canale Native Messaging Python sono percorsi distinti. Browser CDP isolato non equivale al desktop dell'utente. Codice di una primitiva non significa che la chat possa invocarla o che sia stata collaudata in Windows.

## 4. Cosa e stato osservato davvero

Prove singole eseguite dall'utente Windows/Gemini, non dall'assistente sul PC:

| ID | Evidenza | Limite |
|---|---|---|
| e2e-footer-003 | screenshot nel pannello | non prova ricezione nella chat |
| e2e-text-004 | JSON nella chat, risposta Gemini con ID e dimensioni, SENT_CONFIRMED | non prova immagine al modello |
| e2e-image-005 | risposta immagine non disponibile | prova non riuscita; non identifica da sola un guasto upload |
| e2e-image-006 | immagine allegata e JSON nella conversazione, descrizione visiva del modello, SENT_CONFIRMED — ATTACHMENT_VERIFIED (conferma utente) | percorso assistito, non certificazione generale |

Per e2e-image-006 lo screenshot utente del 1 novembre alle 03:12 CET mostra Gemini descrivere il pulsante rosso STOP DESKTOP e il pannello in basso a destra. E la prova positiva screenshot -> stessa chat -> lettura visiva. L'originale non e versionato qui: questo e un resoconto con provenienza, non un artefatto crittograficamente verificabile o una ricevuta server. Non dichiarare che il successivo STOP sia stato premuto: era stato richiesto ma non e arrivata conferma.

Il test positivo non va ripetuto solo per rimettere in contesto la nuova IA. Ripeterlo solo se una modifica o un requisito aperto richiede una nuova prova, con consenso e ID nuovo. Non riutilizzare gli ID storici come comandi live.

## 5. Semantica del percorso immagine

La tranche manifest 0.2.1 usa un solo tentativo di allegato e di invio. Il paste sintetico del File e compatibilita, non prova upload. Preview unica stabile per 3 secondi e assenza degli indicatori rilevati consentono la conferma umana. verification=user-confirmed non e verifica crittografica. Preview cambiata o ambigua non autorizza l'invio.

ATTACHMENT_UNCERTAIN_HALT e SEND_UNCERTAIN_HALT sono terminali: niente secondo upload, secondo invio o retry automatico. SENT_CONFIRMED richiede l'immagine nel messaggio uscente correlato; la risposta visiva del modello aggiunge evidenza per la singola prova. Preservare bozze e allegati preesistenti. Non eseguire cronologia, esempi o risposte ancora in streaming.

Per una nuova prova separare il comando immediato dalle istruzioni sul risultato futuro. Il prompt precedente che li mescolava ha prodotto una risposta prematura di Gemini. Non confondere questo episodio con un difetto dimostrato dell'upload.

## 6. Copie, incidente PowerShell e allineamento non concluso

Windows attiva: C:\Users\ugopl\omninode-github. Seconda copia del tentativo: A:\omninode-clean-20261101-011658. A: aveva un desktop.ini in .git/refs; nessuna riparazione e confermata. Altri backup, branch, stash e VPS sono elencati in ../RESUME.md e vanno preservati.

Alle 03:18 CET il primo script allegato ha fallito il parsing: $repo: in una stringa espandibile va delimitato ${repo}:. Il blocco non e stato eseguito. E stato rimandato il file corretto, ma non e arrivato l'output ALLINEAMENTO LOCALE VERIFICATO o un altro riscontro di esecuzione. Non dichiarare allineati C:, A: e Drive.

Il file consegnato non e nel repository e non e stato eseguito o validato con PowerShell Windows dall'assistente. Prevedeva backup prima di quarantena di metadati riconosciuti, controlli Git, fast-forward e ZIP/manifest SHA256; drive_upload_verified restava false. Non trattare il piano come operazione eseguita.

Il suo target fissato 9316f6b2 diventa vecchio con nuovi commit: puo arrestarsi sul remoto avanzato anche se i nuovi commit sono solo documentali. Non aggirare il controllo, forzare il branch o riportare HEAD indietro. Verificare e approvare un riferimento nuovo prima di rigenerare lo script. Per nuovi script PowerShell verificare il parsing prima di pubblicarli, poi testare in un ambiente adatto; non chiamare test Windows una verifica testuale.

Non cancellare refs/oggetti/lock per far passare fsck. Diagnosi e backup verificato prima di qualsiasi recupero; i file desktop.ini non riconosciuti come metadati Windows non vanno spostati automaticamente. Non sincronizzare .git con Drive. Usare snapshot versionati e verificare hash prima di dichiarare una copia cloud allineata. Non caricare backup .git, credenziali o log console.

## 7. Build e test da eseguire con un esecutore reale

Seguire ../BUILD.md e i manifest attuali. Non installare dipendenze globalmente o nel venv sbagliato. La baseline dichiara Go 1.26.0; gateway CI Python 3.11 e desktop CI 3.12: ricontrollare i file, non fissare per sempre queste versioni.

Dal modulo omniclient: go mod verify; go vet ./...; go test -count=1 ./.... Il race test dipende da piattaforma, CGO e toolchain C.

Dalla root, nel contesto previsto dalla CI: node --test omniclient/extension/*.test.cjs. Per desktop leggere i workflow reali e distinguere mock, fixture e Windows fisico. native-browser e opt-in con host sintetico; l'ambiente Chromium di fixture non va usato per account reali.

Gateway, in venv dedicato da node1-gateway: python -m pip install -r requirements-test.txt; python -m playwright install chromium; python -m pytest -v. Installazioni di sistema, installer Windows con --apply e modifiche persistenti richiedono le autorizzazioni appropriate.

Non reinstallare o ricaricare host/estensione soltanto per un commit documentale. Sorgenti, runtime installato, processo avviato e binario distribuito sono stati diversi. Nessun test nuovo e stato eseguito per il solo fatto di scrivere questo handover.

## 8. Piano per finire, con accettazione

1. Ricostruire strumenti e stato reale; verificare il commit documentale e CI. Risolvere l'allineamento copie senza cancellare recuperi, se necessario al lavoro.
2. Chiudere test del percorso allegato/invio: bozza, allegato precedente, upload lento/fallito, preview sostituita, duplicati, click unico, STOP/scadenza/navigazione. Accettazione: nessun invio o retry in stato incerto.
3. Propagazione STOP nativo/browser e race. Accettazione: revoca blocca nuove azioni e invalida quelle pendenti, nelle due direzioni; input gia consegnati al sistema operativo non sono annullabili per promessa.
4. Persistenza/idempotenza. Revisionare i registri esistenti, non crearne un altro senza analisi. Accettazione: crash/restart non causa replay di effetti incerti e le correlazioni restano verificabili.
5. Unicode, DPI, multi-monitor e azioni desktop necessarie nella chat. Accettazione: test appropriati piu prove fisiche mirate, policy e consenso per ogni perimetro; nessuna inferenza dal solo codice della primitiva.
6. Hardening Go, trasporti realmente avviati e canali locali. Preservare mTLS/ACL, TLS 1.3 e creazione workspace confinata/esclusiva. Nessuna esposizione pubblica o shell remota arbitraria.
7. Seconda IA tramite chat reale e consenso ai dati condivisi. Accettazione: incarico inviato, risposta ricevuta e contributo correlato, non semplice tab aperta. Un solo responsabile per patch.
8. Matrice requisiti/prove e documentazione finale. Dichiarare implementato, testato, osservato e residuo separatamente. Non chiamare il progetto finito finche il ciclo completo richiesto e le condizioni di arresto non sono provati. Merge, release, deploy e cambi dei servizi richiedono gate separati.

## 9. Divieti e passaggio successivo

Niente reset distruttivi, force push, pulizia di stash/branch, porte pubbliche, fallback plaintext, bypass login/CAPTCHA, privilegi automatici o segreti in chat/Git/log. Il consenso desktop non autorizza qualsiasi scrittura esterna. Fermarsi ai gate specifici con destinatario, file e contenuto esatti.

A fine tranche aggiornare CURRENT_STATUS.md e NEXT_STEPS.md con SHA, comandi realmente eseguiti, esito dei check, prova reale e limiti. Conservare la provenienza delle evidenze; non trasformare piani o output storici in successi correnti. La prossima IA deve poter ripartire leggendo questi file senza richiedere tutta la vecchia conversazione.
