# Security - OmniNode

## Principi di Sicurezza

1. **Defense in Depth**: Multipli strati di protezione (rete, applicazione, dati)
2. **Least Privilege**: Ogni componente opera con minimi privilegi necessari
3. **Zero Trust**: Nessuna fiducia implicita, verificare sempre identità e autorizzazioni
4. **Audit by Default**: Tutte le operazioni sono tracciate e immutabili

## Confini di Sicurezza

### Perimetro di Rete

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RETE CLIENT                                   │
│  ┌─────────────┐                                                    │
│  │  omniclient │  ← localhost only (127.0.0.1)                     │
│  │  :8080      │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         │ HTTPS                                                     │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │  Gateway    │  ← Firewall: solo IP autorizzati                  │
│  │  :8000      │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         │ MQTT over TLS                                             │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │  MQTT       │  ← Broker: autenticazione + TLS                   │
│  │  Broker     │                                                    │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Confini Applicativi

| Componente | Input | Output | Trust Boundary |
|------------|-------|--------|----------------|
| MCP Server | MCP Client | CDP, Gateway | Client locale attendibile |
| CDP Agent | MCP Server | Chrome :9222 | localhost only |
| Gateway Client | MCP Server | Gateway HTTP | Rete esterna (non attendibile) |
| FastAPI | Gateway Client | Task Store, MQTT | Rete interna (parzialmente attendibile) |
| MQTT Service | Gateway, Client | Broker MQTT | Rete esterna (non attendibile) |
| Browser Runtime | MQTT, FastAPI | Chrome CDP | Isolato, policy-enforced |

## Hardening

### omniclient (Go)

```bash
# 1. Compilazione sicura
go build -ldflags="-s -w" -o omniclient .

# 2. Esecuzione con utente dedicato
useradd -r -s /bin/false omniclient
chown omniclient:omniclient /opt/omniclient
sudo -u omniclient /opt/omniclient/omniclient

# 3. Firewall localhost
ufw deny from any to any port 8080
ufw allow from 127.0.0.1 to any port 8080
```

**Configurazione sicura** (`config.yaml`):
```yaml
gateway_url: https://gateway.example.com  # HTTPS obbligatorio
mqtt_broker: mqtts://broker.example.com:8883  # TLS
cdp_port: 9222
cdp_allow_remote: false  # Solo localhost
mcp_auth_token: ${MCP_AUTH_TOKEN}  # Env var, mai hardcoded
```

### node1-gateway (Python)

```bash
# 1. Virtualenv isolato
python -m venv /opt/omni/gateway
source /opt/omni/gateway/bin/activate

# 2. Utente dedicato
useradd -r -s /bin/false omni-gateway
chown -R omni-gateway:omni-gateway /opt/omni/gateway

# 3. Firewall
ufw allow from 10.0.0.0/8 to any port 8000  # Solo rete interna
ufw deny from any to any port 8000  # Blocca resto
```

**Configurazione sicura** (`.env`):
```
# HTTPS obbligatorio (reverse proxy con TLS)
BIND_HOST=127.0.0.1
BIND_PORT=8000

# MQTT con TLS e autenticazione
MQTT_BROKER=mqtts://broker.example.com:8883
MQTT_USERNAME=omni_gateway
MQTT_PASSWORD=${MQTT_PASSWORD}  # Env var
MQTT_CLIENT_CERT=/etc/omni/certs/gateway.crt
MQTT_CLIENT_KEY=/etc/omni/certs/gateway.key

# Audit logging
AUDIT_LOG_PATH=/var/log/omni/audit.jsonl
AUDIT_LOG_CHMOD=0640  # Solo root + gruppo omni-audit

# Policy engine
POLICY_ENFORCE=true
POLICY_MAX_CONCURRENT_BROWSERS=5
POLICY_TIMEOUT_MS=30000
```

### Chrome CDP

```bash
# 1. Esecuzione con utente dedicato
google-chrome --remote-debugging-port=9222 \\
  --user-data-dir=/opt/chrome-profiles/omni \\
  --no-first-run \\
  --disable-extensions \\
  --disable-gpu

# 2. Firewall localhost
ufw deny from any to any port 9222
ufw allow from 127.0.0.1 to any port 9222

# 3. Nessuna esposizione pubblica
# MAI usare --remote-debugging-address=0.0.0.0
```

### MQTT Broker (Mosquitto)

```conf
# /etc/mosquitto/mosquitto.conf
listener 8883
protocol mqtt

# TLS obbligatorio
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/broker.crt
keyfile /etc/mosquitto/certs/broker.key
require_certificate true

# Autenticazione
password_file /etc/mosquitto/pwfile
allow_anonymous false

# ACL
acl_file /etc/mosquitto/acl
```

**ACL** (`/etc/mosquitto/acl`):
```
# omniclient
topic readwrite omni/heartbeat client_omniclient_*
topic read omni/browser/result client_omniclient_*
topic write omni/browser/request client_omniclient_*

# gateway
topic readwrite omni/# client_gateway
```

## Incident Response

### Scenario 1: CDP Esposto su Rete Pubblica

**Rilevamento**:
```bash
# Scan porte
nmap -p 9222 gateway.example.com

# Log audit
grep "cdp_remote" /var/log/omni/audit.jsonl
```

**Contenimento**:
1. Bloccare porta 9222 su firewall: `ufw deny 9222/tcp`
2. Terminare processo Chrome: `pkill -f "remote-debugging-port=9222"`
3. Ruotare credenziali MQTT e API keys

**Eradicazione**:
1. Rimuovere configurazione errata da script di avvio
2. Aggiornare playbook Ansible/Terraform
3. Riavviare Chrome con configurazione corretta

**Recupero**:
1. Riavviare Chrome: `google-chrome --remote-debugging-port=9222 --user-data-dir=/opt/chrome-profiles/omni`
2. Verificare connettività: `curl http://127.0.0.1:9222/json/version`
3. Ripristinare task in esecuzione da backup

### Scenario 2: MQTT senza TLS

**Rilevamento**:
```bash
# Packet capture
tcpdump -i any port 1883 -w mqtt_capture.pcap

# Log gateway
grep "mqtt://" /var/log/omni/gateway.log  # Cerca connessioni non TLS
```

**Contenimento**:
1. Bloccare porta 1883: `ufw deny 1883/tcp`
2. Forzare riconnessione client: `systemctl restart omniclient`
3. Abilitare solo mqtts://8883

**Eradicazione**:
1. Aggiornare configurazione client e gateway
2. Rigenerare certificati MQTT
3. Implementare monitoraggio connessioni non-TLS

### Scenario 3: Audit Log Manomesso

**Rilevamento**:
```bash
# Controllo integrità
sha256sum /var/log/omni/audit.jsonl
# Confronta con hash salvato in luogo sicuro

# Controllo gap temporali
awk -F'"timestamp"' '{print $2}' /var/log/omni/audit.jsonl | \\
  sort | uniq -c | grep -B1 -A1 "00:00:00"
```

**Contenimento**:
1. Isolare sistema: `ufw default deny`
2. Preservare evidenza: `cp /var/log/omni/audit.jsonl /evidence/`
3. Notificare security team

**Eradicazione**:
1. Identificare utente/processo: `ausearch -f /var/log/omni/audit.jsonl`
2. Revocare accessi: `usermod -L username`
3. Implementare audit log remoto (syslog/SIEM)

## Checklist Sicurezza (Pre-Produzione)

- [ ] HTTPS abilitato su gateway (certificato valido, non self-signed)
- [ ] MQTT over TLS (mqtts://) con certificati client
- [ ] CDP accessibile solo da localhost (firewall + bind 127.0.0.1)
- [ ] Utenti dedicati per ogni servizio (omniclient, omni-gateway, chrome)
- [ ] Secret in env var o vault (mai hardcoded)
- [ ] Audit logging attivo e immutabile (append-only, backup remoto)
- [ ] Policy engine abilitato con limiti configurati
- [ ] Firewall configurato (ufw/iptables)
- [ ] Monitoraggio attivo (log aggregation, alerting)
- [ ] Backup e recovery testati
