#!/usr/bin/env python3
"""Idempotent, fail-safe OmniNode Oracle bootstrap.

Default mode is dry-run. Use --apply to make changes and --enable-services
to enable/start systemd units. This script never creates private keys or
opens firewall ports.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BootstrapConfig:
    repo_root: Path
    service_user: str = "omninode"
    opt_root: Path = Path("/opt/omninode")
    etc_root: Path = Path("/etc/omninode")
    log_root: Path = Path("/var/log/omninode")
    workspace_root: Path = Path("/opt/omninode/workspace")
    backup_root: Path = Path("/var/backups/omninode")

    @property
    def cert_root(self) -> Path:
        return self.etc_root / "certs"

    @property
    def required_certs(self) -> tuple[Path, ...]:
        return (
            self.cert_root / "ca.crt",
            self.cert_root / "gateway.crt",
            self.cert_root / "gateway.key",
            self.cert_root / "worker-1.crt",
            self.cert_root / "worker-1.key",
        )

    @property
    def required_env_files(self) -> tuple[Path, ...]:
        return (
            self.etc_root / "omninode-gateway.env",
            self.etc_root / "omninode-worker.env",
        )


class BootstrapError(RuntimeError):
    pass


def run(command: list[str], dry_run: bool) -> None:
    printable = " ".join(command)
    if dry_run:
        print(f"[DRY-RUN] {printable}")
        return
    print(f"[RUN] {printable}")
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise BootstrapError(
            f"command failed ({result.returncode}): {printable}\n{result.stderr.strip()}"
        )


def user_exists(user: str, dry_run: bool) -> bool:
    result = subprocess.run(["id", user], check=False, capture_output=True, text=True)
    return result.returncode == 0


def ensure_directory(path: Path, owner: str, dry_run: bool) -> bool:
    if path.exists():
        if not path.is_dir():
            raise BootstrapError(f"{path} esiste ma non è una directory")
        return False
    run(["sudo", "mkdir", "-p", str(path)], dry_run)
    run(["sudo", "chown", f"{owner}:{owner}", str(path)], dry_run)
    run(["sudo", "chmod", "0750", str(path)], dry_run)
    return True


def backup_file(path: Path, backup_root: Path, dry_run: bool) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_dir = backup_root / stamp
    target = backup_dir / path.relative_to("/")
    run(["sudo", "mkdir", "-p", str(target.parent)], dry_run)
    run(["sudo", "cp", "-a", str(path), str(target)], dry_run)
    return target


def install_file(source: Path, target: Path, mode: str, owner: str, config: BootstrapConfig, dry_run: bool) -> bool:
    if target.exists():
        if target.read_bytes() == source.read_bytes():
            print(f"[UNCHANGED] {target}")
            return False
        backup_file(target, config.backup_root, dry_run)
    run(["sudo", "mkdir", "-p", str(target.parent)], dry_run)
    run(["sudo", "install", "-o", owner, "-g", owner, "-m", mode, str(source), str(target)], dry_run)
    return True


def preflight(config: BootstrapConfig) -> None:
    repo = config.repo_root
    required_sources = (
        repo / "deploy/systemd/omninode-gateway.service",
        repo / "deploy/systemd/omninode-worker.service",
    )
    for source in required_sources:
        if not source.is_file():
            raise BootstrapError(f"file sorgente mancante: {source}")

    for cert in config.required_certs:
        if not cert.is_file():
            raise BootstrapError(
                f"certificato/chiave mancante: {cert}."
                " Provisionare i certificati fuori da Git prima di --apply."
            )

    for env_file in config.required_env_files:
        if not env_file.is_file():
            raise BootstrapError(
                f"file ambiente mancante: {env_file}."
                " Crearlo manualmente con permessi 0600; non inserire segreti in Git."
            )


def bootstrap(config: BootstrapConfig, apply: bool, enable_services: bool) -> None:
    dry_run = not apply
    preflight(config)

    if not user_exists(config.service_user, dry_run):
        run(["sudo", "useradd", "--system", "--shell", "/usr/sbin/nologin", config.service_user], dry_run)
    else:
        print(f"[UNCHANGED] utente {config.service_user}")

    for directory in (config.opt_root, config.log_root, config.etc_root, config.cert_root, config.workspace_root):
        ensure_directory(directory, config.service_user, dry_run)

    changed = False
    for name in ("omninode-gateway.service", "omninode-worker.service"):
        source = config.repo_root / "deploy/systemd" / name
        target = Path("/etc/systemd/system") / name
        changed |= install_file(source, target, "0644", "root", config, dry_run)

    if not dry_run and changed:
        run(["sudo", "systemctl", "daemon-reload"], dry_run)

    if enable_services:
        if not apply:
            raise BootstrapError("--enable-services richiede anche --apply")
        for name in ("omninode-gateway.service", "omninode-worker.service"):
            run(["sudo", "systemctl", "enable", "--now", name], dry_run)
    else:
        print("[SAFE] servizi non abilitati né avviati: usare --enable-services solo dopo approvazione")

    print("[SUCCESS] bootstrap completato" + (" in dry-run" if dry_run else ""))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OmniNode Oracle bootstrap")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true", help="applica le modifiche; senza questo flag è dry-run")
    parser.add_argument("--enable-services", action="store_true", help="abilita e avvia i servizi systemd")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = BootstrapConfig(repo_root=args.repo_root.resolve())
    try:
        bootstrap(config, apply=args.apply, enable_services=args.enable_services)
    except BootstrapError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
