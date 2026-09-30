# Next Steps - OmniNode

## Priorità Alta (Q4 2024)

### 1. Autenticazione e Autorizzazione MCP

**Stato**: ❌ Non implementato
**Sforzo**: 3-5 giorni
**Impatto**: Critico per produzione

**Checklist**:
- [ ] Implementare middleware auth su mcp_server.go (JWT o API key)
- [ ] Aggiungere config `mcp_auth_token` in config.yaml
- [ ] Testare con MCP client (Claude Desktop, Cline)
- [ ] Documentare in MCP_SETUP.md

**Criteri di Accettazione**:
- MCP server rifiuta richieste senza token valido
- Token configurabile via env var
- Log audit per tentativi falliti

### 2. Persistenza Task Store

**Stato**: ❌ Non implementato (in-memory only)
**Sforzo**: 5-7 giorni
**Impatto**: Alto (recupero dopo restart)

**Checklist**:
- [ ] Scegliere backend (SQLite, PostgreSQL, Redis)
- [ ] Implementare interfaccia TaskStore (save, load, update, delete)
- [ ] Migrare task_store.py da in-memory a persistente
- [ ] Testare recovery dopo crash gateway
- [ ] Backup automatico (cron o systemd timer)

**Criteri di Accettazione**:
- Task sopravvivono a restart gateway
- Query per stato task (pending, completed, failed)
- Cleanup automatico task > 30 giorni

### 3. TLS per MQTT e HTTP

**Stato**: ❌ Non implementato (plaintext)
**Sforzo**: 2-3 giorni
**Impatto**: Critico per sicurezza

**Checklist**:
- [ ] Generare certificati TLS (openssl o Let's Encrypt)
- [ ] Configurare Mosquitto per mqtts://8883
- [ ] Aggiornare mqtt_client.go per TLS
- [ ] Aggiornare mqtt_service.py per TLS
- [ ] Configurare reverse proxy (nginx) per HTTPS gateway
- [ ] Testare connessioni sicure

**Criteri di Accettazione**:
- MQTT solo su mqtts:// (porta 1883 bloccata)
- HTTPS su gateway (porta 443)
- Certificati validi (non self-signed in produzione)

## Priorità Media (Q1 2025)

### 4. Multi-Sessione Browser

**Stato**: ❌ Single-instance
**Sforzo**: 7-10 giorni
**Impatto**: Alto (scalabilità)

**Checklist**:
- [ ] Implementare BrowserSession class in browser_runtime.py
- [ ] Gestire multiple istanze Chrome (porte CDP dinamiche)
- [ ] Session isolation (cookie, localStorage, cache)
- [ ] Limiti per workspace (max sessioni concurrenti)
- [ ] Cleanup sessioni idle (timeout 30 min)

**Criteri di Accettazione**:
- 5+ sessioni browser concurrenti
- Isolamento completo tra sessioni
- Memory usage < 2GB per 5 sessioni

### 5. Monitoring e Alerting

**Stato**: ❌ Non implementato
**Sforzo**: 3-5 giorni
**Impatto**: Medio (observability)

**Checklist**:
- [ ] Integrare Prometheus metrics (go_prometheus_client)
- [ ] Esportare metrics: request_count, latency, error_rate
- [ ] Dashboard Grafana (template JSON)
- [ ] Alert: error_rate > 5%, latency_p99 > 5s
- [ ] Log aggregation (Loki o ELK)

**Criteri di Accettazione**:
- Dashboard con metrics real-time
- Alert su Slack/PagerDuty
- Log queryabili per task_id, workspace_id

### 6. Rate Limiting e Quotas

**Stato**: ❌ Non implementato
**Sforzo**: 2-3 giorni
**Impatto**: Medio (fairness, costi)

**Checklist**:
- [ ] Implementare rate limiter (token bucket) in policy_engine.py
- [ ] Config per workspace: requests_per_minute, requests_per_day
- [ ] Quota browser: minutes_per_day, screenshots_per_day
- [ ] Response 429 Too Many Requests con Retry-After header
- [ ] Metrics per quota usage

**Criteri di Accettazione**:
- Rate limiting funzionante a 10 req/min default
- Quota enforcement per workspace
- Alert quando quota > 80%

## Priorità Bassa (Q2 2025)

### 7. Plugin System

**Stato**: ❌ Non implementato
**Sforzo**: 10-14 giorni
**Impatto**: Medio (extensibility)

**Checklist**:
- [ ] Definire interfaccia Plugin (Python: ABC, Go: interface)
- [ ] Implementare loader dinamico (importlib, plugin pkg)
- [ ] Sandbox plugin (seccomp, gVisor)
- [ ] Registry plugin (git submodule o marketplace)
- [ ] Documentare SDK per sviluppatori

**Criteri di Accettazione**:
- Plugin example funzionante (es. browser extension)
- Isolamento sicurezza (plugin non può accedere a file system)
- Hot reload plugin (senza restart gateway)

### 8. GraphQL API

**Stato**: ❌ Non implementato (solo REST + MQTT)
**Sforzo**: 5-7 giorni
**Impatto**: Basso (developer experience)

**Checklist**:
- [ ] Integrare Strawberry (Python) o gql (Go)
- [ ] Definire schema GraphQL (Query, Mutation, Subscription)
- [ ] Resolver per task, browser, ops
- [ ] Subscription per task status (real-time)
- [ ] Documentare con GraphiQL

**Criteri di Accettazione**:
- Query: `task(id: "uuid") { status, result }`
- Mutation: `browserNavigate(url: "...") { taskId }`
- Subscription: `taskStatusChanged(taskId: "...") { status }`

### 9. CLI Tool

**Stato**: ❌ Non implementato
**Sforzo**: 3-5 giorni
**Impatto**: Basso (developer experience)

**Checklist**:
- [ ] Scegliere framework (cobra per Go, click per Python)
- [ ] Comandi: `omni task list`, `omni browser navigate`, `omni ops plan`
- [ ] Output: table, JSON, YAML
- [ ] Auth integration (login, logout, token refresh)
- [ ] Publish su PyPI e Homebrew

**Criteri di Accettazione**:
- CLI funzionale per operazioni comuni
- Documentazione help (`omni --help`)
- CI/CD per release automatiche

## Backlog (Futuro)

- [ ] Supporto WebSocket per MCP (oltre HTTP)
- [ ] Integration con Kubernetes (operator CRD)
- [ ] UI dashboard (React + Tailwind)
- [ ] Supporto Firefox (oltre Chrome CDP)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] gRPC per comunicazione client-gateway
- [ ] Caching layer (Redis) per screenshot e DOM
- [ ] ML-based anomaly detection (audit logs)

## Dipendenze Critiche

| Task | Dipende da | Bloccante |
|------|------------|-----------|
| Autenticazione MCP | - | No |
| Persistenza Task Store | - | No |
| TLS per MQTT | - | No |
| Multi-Sessione | Persistenza Task Store | Sì |
| Monitoring | TLS | No |
| Rate Limiting | Autenticazione | No |

## Milestone

| Milestone | Data Target | Task Inclusi |
|-----------|-------------|--------------|
| M1: Security Hardening | 2024-12-31 | Auth MCP, TLS MQTT/HTTP |
| M2: Production Ready | 2025-03-31 | Persistenza, Multi-Sessione, Monitoring |
| M3: Scale | 2025-06-30 | Rate Limiting, Plugin System, CLI |
