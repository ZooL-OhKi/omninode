# Roadmap - OmniNode

## Implementato (Q3 2024)

### Core Architecture
- ✅ **MCP Server (Go)**: Server MCP con tool browser_* e ops_*
- ✅ **CDP Agent (Go)**: Integrazione Chrome DevTools Protocol
- ✅ **Gateway Client (Go)**: HTTP client verso node1-gateway
- ✅ **MQTT Client (Go)**: Pub/sub asincrono per task/results
- ✅ **FastAPI Gateway (Python)**: REST API + WebSocket
- ✅ **MQTT Service (Python)**: Messaggistica asincrona
- ✅ **Task Store (Python)**: In-memory store per task
- ✅ **Policy Engine (Python)**: Autorizzazioni e limiti base

### Browser Automation
- ✅ **browser_navigate**: Navigazione a URL
- ✅ **browser_click**: Click su elementi (CSS selector)
- ✅ **browser_type**: Digitazione testo (input fields)
- ✅ **browser_screenshot**: Screenshot full-page e viewport
- ✅ **CDP locale**: Chrome su porta 9222

### Operations
- ✅ **ops_terraform_plan**: Esecuzione `terraform plan`
- ✅ **ops_terraform_apply**: Esecuzione `terraform apply`
- ✅ **Terraform CLI integration**: Parsing stdout/stderr

### Infrastructure
- ✅ **Audit Logging**: Log JSONL immutabile
- ✅ **Workspace Manager**: Gestione contesti multi-tenant
- ✅ **Heartbeat**: Health check periodici client→gateway
- ✅ **WebSocket Server**: Connessioni bidirezionali

### Documentation
- ✅ README.md, ARCHITECTURE.md, SECURITY.md
- ✅ BUILD.md, NEXT_STEPS.md, ROADMAP.md
- ✅ docs/AI_ONBOARDING.md, OPERATIONS_RUNBOOK.md, REPOSITORY_MAP.md
- ✅ omniclient/README.md, HANDOFF.md, MCP_SETUP.md

## In Progress (Q4 2024)

### Security Hardening
- 🔄 **Autenticazione MCP**: JWT/API key middleware (50%)
- 🔄 **TLS MQTT**: Certificati client/server (30%)
- 🔄 **HTTPS Gateway**: Reverse proxy nginx (20%)

### Reliability
- 🔄 **Task Store Persistente**: SQLite backend (40%)
- 🔄 **Retry Logic**: Exponential backoff per MQTT (60%)
- 🔄 **Circuit Breaker**: Gateway client fallback (30%)

### Developer Experience
- 🔄 **MCP Setup Guide**: Config Claude Desktop (80%)
- 🔄 **Test Suite**: Unit + integration test (70%)
- 🔄 **CI/CD**: GitHub Actions workflow (50%)

## Backlog (Q1-Q2 2025)

### Scalability
- ⏳ **Multi-Sessione Browser**: 5+ Chrome concurrenti
- ⏳ **Load Balancing**: Multiple gateway instances
- ⏳ **Caching**: Redis per screenshot/DOM

### Observability
- ⏳ **Prometheus Metrics**: request_count, latency, error_rate
- ⏳ **Grafana Dashboard**: Template JSON
- ⏳ **Distributed Tracing**: OpenTelemetry

### Extensibility
- ⏳ **Plugin System**: SDK per sviluppatori
- ⏳ **GraphQL API**: Query, Mutation, Subscription
- ⏳ **CLI Tool**: omni task list, browser navigate

### Platform
- ⏳ **Kubernetes Operator**: CRD per OmniNode
- ⏳ **Helm Chart**: Deploy one-command
- ⏳ **Docker Compose**: Dev environment

## Timeline

```
2024 Q3        Q4           2025 Q1          Q2
│──────────────│─────────────│───────────────│─────────────│
│ Implementato │ Hardening   │ Scalability   │ Platform    │
│ Core Arch    │ Auth + TLS  │ Multi-Session │ K8s + Helm  │
│ Browser Auto │ Persistence │ Monitoring    │ CLI + UI    │
│ Ops          │ Testing     │ Rate Limit    │ Plugins     │
```

## Metriche di Successo

| Metrica | Target | Attuale |
|---------|--------|---------|
| Uptime Gateway | 99.9% | N/A (dev) |
| Latency p99 | <500ms | N/A (dev) |
| Error Rate | <1% | N/A (dev) |
| Task Recovery | 100% | 0% (in-memory) |
| Security Audit | 0 critical | Pending |

## Release Schedule

| Versione | Data | Feature |
|----------|------|---------|
| v0.1.0 | 2024-09-30 | Alpha (dev locale) |
| v0.2.0 | 2024-12-31 | Beta (security hardening) |
| v1.0.0 | 2025-03-31 | GA (production ready) |
| v1.1.0 | 2025-06-30 | Scale (multi-session, monitoring) |
