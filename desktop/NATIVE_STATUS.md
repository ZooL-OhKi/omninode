# Host Native Messaging

[Stato corrente](../docs/CURRENT_STATUS.md). Canale stdin/stdout JSON con lunghezza prefissata, input massimo 128 KiB e output 1 MiB; non e MCP o HTTP.

native_host.py verifica l'origine browser rispetto a OMNINODE_NATIVE_ORIGIN prima di leggere le richieste. Il bootstrap accetta un ping esatto che risponde con versione protocollo, desktop_active=false e consent_required=true, poi termina prima di importare gli strumenti desktop o Tk. Non crea sessioni e non restituisce credenziali.

Per attivare il desktop e necessario open con conversazione valida, seguito dal consenso locale. Le azioni hanno session_id, sequence, action e args. La sequenza e consumata prima dell'effetto: dopo errore o timeout non ripetere input automaticamente. La credenziale resta nell'host.

STOP/disconnessione/scadenza devono revocare gli input successivi, ma non annullano eventi consegnati; disconnect durante chiamate OS bloccanti non e immediato. [Preview](SCREEN_STATUS.md) gestisce il limite del messaggio. La nuova diagnostica non autorizza pagine o altre IA e non elimina il consenso.

Bootstrap verificato con 7 test e codec reale. Il nuovo smoke di setup/launcher Windows attende CI; UI di consenso, controllo fisico e collegamento automatico alla conversazione restano non dimostrati. Nessuna modifica a MQTT, ACL, workspace Go o PC dell'utente.
