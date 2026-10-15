# OmniNode Oracle Free Deployment Guide
1. Clona il repository in `/opt/omninode`.
2. Configura il file `.env` (non tracciato).
3. Installa i servizi systemd da `deploy/systemd/`.
4. Abilita e avvia con `systemctl enable --now omninode-gateway`.