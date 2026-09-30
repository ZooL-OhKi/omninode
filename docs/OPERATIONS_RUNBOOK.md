# Operations Runbook - OmniNode

## Preflight Check

Prima di avviare il sistema, verificare:

### 1. Dipendenze Esterne

```bash
# MQTT Broker
systemctl status mosquitto
mosquitto_sub -t "omni/#" -v

# Chrome CDP
curl http://localhost:9222/json/version

# Porta gateway libera
netstat -tlnp | grep :8000
```

### 2. Configurazione

```bash
# node1-gateway
cat node1-gateway/.env

# omniclient
cat omniclient/config.yaml
```

### 3. Permessi

```bash
ls -la /var/log/omni/
ls -la /opt/chrome-profiles/omni/
```

## Avvio

### Sequenza di Avvio

1. **MQTT Broker**: `mosquitto -c /etc/mosquitto/mosquitto.conf -d`
2. **Chrome con CDP**: `google-chrome --remote-debugging-port=9222 --user-data-dir=/opt/chrome-profiles/omni &`
3. **Gateway**: `cd node1-gateway && uvicorn main:app --host 0.0.0.0 --port 8000 &`
4. **omniclient**: `cd omniclient && ./omniclient &`

### Verifica Avvio

```bash
curl http://localhost:8000/health
curl http://localhost:8080/health
mosquitto_sub -t "omni/#" -v
```

## Monitoraggio

### Metriche Chiave

| Metrica | Soglia | Azione |
|---------|--------|--------|
| Gateway CPU | >80% per 5 min | Scalare verticalmente |
| Gateway Memory | >90% | Restart + investigare leak |
| MQTT Queue Depth | >1000 messaggi | Scalare broker |
| CDP Response Time | >5s | Restart Chrome |
| Audit Log Size | >10GB | Rotazione log |

### Log da Monitorare

```bash
tail -f /var/log/omni/gateway.log | grep -E "ERROR|WARN"
tail -f /var/log/omni/omniclient.log | grep -E "ERROR|WARN"
tail -f /var/log/omni/audit.jsonl
journalctl -u mosquitto -f
```

## Incidenti

### 1. Gateway Non Risponde

```bash
ps aux | grep uvicorn
netstat -tlnp | grep 8000
tail -100 /var/log/omni/gateway.log
systemctl restart omninode-gateway
curl http://localhost:8000/health
```

### 2. Chrome CDP Disconnesso

```bash
ps aux | grep chrome
netstat -tlnp | grep 9222
pkill -f "remote-debugging-port=9222"
google-chrome --remote-debugging-port=9222 --user-data-dir=/opt/chrome-profiles/omni &
curl http://localhost:9222/json/version
```

### 3. MQTT Broker Iriraggiungibile

```bash
systemctl status mosquitto
mosquitto_sub -t "omni/#" -v
systemctl restart mosquitto
```

### 4. Task Store Pieno

```bash
ps aux | grep python
sqlite3 /var/lib/omni/tasks.db "DELETE FROM tasks WHERE status='completed' AND created_at < datetime('now', '-7 days');"
systemctl restart omninode-gateway
```

### 5. Audit Log Corrotto

```bash
python3 -c "import json; [json.loads(l) for l in open('/var/log/omni/audit.jsonl')]"
df -h /var/log/omni/
cp /var/log/omni/audit.jsonl /var/log/omni/audit.jsonl.corrupt.$(date +%Y%m%d%H%M%S)
> /var/log/omni/audit.jsonl
chmod 640 /var/log/omni/audit.jsonl
systemctl restart omninode-gateway
```

## Shutdown

```bash
pkill -f omniclient
systemctl stop omninode-gateway
pkill -f "remote-debugging-port=9222"
systemctl stop mosquitto
```

### Backup Pre-Shutdown

```bash
sqlite3 /var/lib/omni/tasks.db ".backup /backup/tasks-$(date +%Y%m%d).db"
tar -czf /backup/audit-$(date +%Y%m%d).tar.gz /var/log/omni/audit.jsonl
tar -czf /backup/config-$(date +%Y%m%d).tar.gz /etc/omni/ /opt/omni/
```

## Manutenzione

### Settimanale

```bash
sqlite3 /var/lib/omni/tasks.db "DELETE FROM tasks WHERE status='completed' AND created_at < datetime('now', '-30 days');"
logrotate -f /etc/logrotate.d/omninode
ls -lh /backup/
```

### Mensile

```bash
apt update && apt upgrade -y
openssl x509 -in /etc/omni/certs/gateway.crt -noout -dates
./scripts/perf_test.sh
```

### Trimestrale

```bash
./scripts/dr_test.sh
./scripts/security_audit.sh
./scripts/capacity_report.sh
```

## Contatti Emergenza

| Ruolo | Nome | Telefono | Email |
|-------|------|----------|-------|
| On-Call | [TBD] | [TBD] | [TBD] |
| Tech Lead | [TBD] | [TBD] | [TBD] |
| DevOps | [TBD] | [TBD] | [TBD] |

## Comandi Utili

```bash
systemctl status omninode-gateway mosquitto
systemctl restart omninode-gateway && sleep 5 && curl http://localhost:8000/health
journalctl -u omninode-gateway --since "1 hour ago" | grep ERROR
watch -n 5 'ps aux | grep -E "(python|omniclient)" | awk "{print \$2, \$3, \$4}"'
```
