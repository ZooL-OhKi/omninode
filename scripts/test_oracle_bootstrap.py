from __future__ import annotations

import os
from pathlib import Path

import pytest

import oracle_bootstrap as bootstrap


def make_config(tmp_path: Path) -> bootstrap.BootstrapConfig:
    repo = tmp_path / "repo"
    deploy = repo / "deploy" / "systemd"
    deploy.mkdir(parents=True)
    (deploy / "omninode-gateway.service").write_text("[Unit]\nDescription=gateway\n")
    (deploy / "omninode-worker.service").write_text("[Unit]\nDescription=worker\n")

    etc = tmp_path / "etc" / "omninode"
    certs = etc / "certs"
    certs.mkdir(parents=True)
    for name in ("ca.crt", "gateway.crt", "gateway.key", "worker-1.crt", "worker-1.key"):
        (certs / name).write_text("certificate")
    (etc / "omninode-gateway.env").write_text("MQTT_HOST=localhost\n")
    (etc / "omninode-worker.env").write_text("OMNINODE_NODE_ID=worker-1\n")

    return bootstrap.BootstrapConfig(
        repo_root=repo,
        opt_root=tmp_path / "opt" / "omninode",
        etc_root=etc,
        log_root=tmp_path / "var" / "log" / "omninode",
        workspace_root=tmp_path / "opt" / "omninode" / "workspace",
        backup_root=tmp_path / "var" / "backups" / "omninode",
    )


def test_dry_run_does_not_install_files(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    executed = []
    monkeypatch.setattr(bootstrap, "run", lambda command, dry_run: executed.append(command))
    monkeypatch.setattr(bootstrap, "user_exists", lambda user, dry_run: True)

    bootstrap.bootstrap(config, apply=False, enable_services=False)

    assert not (Path("/etc/systemd/system/omninode-gateway.service")).exists()
    assert executed


def test_bootstrap_is_idempotent(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    installed = tmp_path / "systemd"
    installed.mkdir()
    monkeypatch.setattr(bootstrap, "user_exists", lambda user, dry_run: True)

    original_install = bootstrap.install_file

    def tracked_install(source, target, mode, owner, config, dry_run):
        target = installed / target.name
        return original_install(source, target, mode, owner, config, dry_run)

    monkeypatch.setattr(bootstrap, "install_file", tracked_install)

    bootstrap.bootstrap(config, apply=True, enable_services=False)
    first = {path.name: path.read_text() for path in installed.glob("*.service")}
    bootstrap.bootstrap(config, apply=True, enable_services=False)
    second = {path.name: path.read_text() for path in installed.glob("*.service")}

    assert first == second


def test_missing_certificate_blocks_apply(tmp_path):
    config = make_config(tmp_path)
    (config.cert_root / "ca.crt").unlink()

    with pytest.raises(bootstrap.BootstrapError, match="certificato/chiave mancante"):
        bootstrap.bootstrap(config, apply=True, enable_services=False)


def test_enable_services_requires_apply(tmp_path):
    config = make_config(tmp_path)

    with pytest.raises(bootstrap.BootstrapError, match="--enable-services richiede anche --apply"):
        bootstrap.bootstrap(config, apply=False, enable_services=True)
