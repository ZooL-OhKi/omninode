#!/bin/bash
# Heartbeat dedicato per OmniNode worker-1.
# Mantiene la registrazione agent_1 -> worker-1 sul gateway.
set -euo pipefail

TS=$(date +%s)

mosquitto_pub \
  -h 127.0.0.1 \
  -p 8883 \
  --cafile /etc/omninode/certs/ca.crt \
  --cert /etc/omninode/certs/worker-1.crt \
  --key /etc/omninode/certs/worker-1.key \
  -t omninode/v1/nodes/worker-1/heartbeat \
  -q 1 \
  -m "{\"node_id\":\"worker-1\",\"agent_id\":\"agent_1\",\"supported_agents\":[\"agent_1\"],\"status\":\"online\",\"timestamp\":$TS}"
