# Indice documentale OmniNode

Aggiornamento: 9 novembre 2026. Indice dei percorsi utili; non è un inventario numerico garantito di tutti i Markdown.

## Ingresso e stato autorevole

- [README](README.md): stato verificato, componenti e limiti recenti.
- [START_HERE](START_HERE.md): ordine di lettura.
- [Handover da zero](docs/ZERO_CONTEXT_HANDOVER.md): bootstrap, architettura, protocollo, diagnostica e recuperi.
- [CURRENT_STATUS](docs/CURRENT_STATUS.md): stato corrente, CI verificata e limiti.
- [AGENTS](AGENTS.md) e [SECURITY](SECURITY.md): regole normative.
- [NEXT_STEPS](NEXT_STEPS.md) e [ROADMAP](ROADMAP.md): residui e accettazione.
- [PROJECT_HANDOVER](PROJECT_HANDOVER.md), [GEMINI_HANDOVER](GEMINI_HANDOVER.md) e [AI_ONBOARDING](docs/AI_ONBOARDING.md): ingressi alternativi.

## Implementazione e operazioni

- [BUILD](BUILD.md), [ARCHITECTURE](ARCHITECTURE.md) e [mappa](docs/REPOSITORY_MAP.md).
- [Estensione](omniclient/extension/README.md), [OmniClient](omniclient/README.md) e [MCP](omniclient/MCP_SETUP.md).
- [Desktop](desktop/README.md), [installer](desktop/INSTALL_STATUS.md), [host](desktop/NATIVE_STATUS.md) e [diagnostica CI](desktop/CI_NATIVE_DIAG.md).
- [Recuperi e copie](RESUME.md): preservare i dettagli storici; non usare vecchi branch come HEAD attuale.
- [Runbook](docs/OPERATIONS_RUNBOOK.md), [produzione](docs/PRODUCTION_READINESS.md) e [pilot](docs/LIVE_PILOT_CERTIFICATION.md).
- [Oracle](deploy/oracle/INSTALL.md), [systemd](deploy/systemd/README.md) e [MQTT/ACL](deploy/mosquitto/README.md): configurazioni, non attestazioni live.

## Precedenza e storia

`README.md`, `CURRENT_STATUS.md` e `ZERO_CONTEXT_HANDOVER.md` descrivono lo stato corrente e prevalgono sulle descrizioni operative datate. `AGENTS.md` e `SECURITY.md` restano normativi.

I documenti storici vengono conservati quando contengono informazioni di recupero, invarianti di sicurezza o cronologia utile. Non interpretare una baseline storica come HEAD corrente né una CI verde come prova di funzionamento completo. Un commit documentale non aggiorna PC, Drive, VPS o CI.
