# Installazione Oracle: procedura da approvare

[Stato corrente](../../docs/CURRENT_STATUS.md). Non e una guida di deploy automatico o una prova che i servizi siano aggiornati.

scripts/oracle_bootstrap.py offre dry-run predefinito e applicazione esplicita; leggerne il piano prima di --apply o --enable-services. Configurare segreti fuori da Git, verificare utente, percorsi, certificati, ACL, backup e provenienza del binario prima di installare unit.

Un clone o pull in /home/ubuntu/omninode non aggiorna il binario archivista in /opt/omninode/omniclient. Non usare systemctl enable --now senza una finestra autorizzata. La prima integrazione desktop non richiede modifiche alle VPS. [Copie da preservare](../../RESUME.md).
