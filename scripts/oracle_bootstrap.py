# OmniNode Oracle Bootstrap Script (Phase 17)
import os
import sys
import subprocess

def run_cmd(cmd):
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed: {res.stderr}")
        sys.exit(res.returncode)
    return res.stdout.strip()

def main():
    print("=== OMNINODE ORACLE BOOTSTRAP (FASE 17) ===")
    
    # 1. Verifica utente di servizio
    try:
        run_cmd("id omninode")
    except SystemExit:
        print("[INFO] Creazione utente di servizio omninode...")
        run_cmd("sudo useradd -r -s /bin/false omninode")

    # 2. Creazione directory operative
    dirs = ["/opt/omninode", "/var/log/omninode", "/etc/omninode/certs"]
    for d in dirs:
        run_cmd(f"sudo mkdir -p {d}")
        run_cmd(f"sudo chown -R omninode:omninode {d}")

    # 3. Copia servizi systemd se presenti nel repo
    if os.path.exists("deploy/systemd/omninode-gateway.service"):
        run_cmd("sudo cp deploy/systemd/omninode-gateway.service /etc/systemd/system/")
        run_cmd("sudo systemctl daemon-reload")
        print("[INFO] Systemd service omninode-gateway installato.")

    print("[SUCCESS] Bootstrap idempotente completato con successo!")

if __name__ == "__main__":
    main()