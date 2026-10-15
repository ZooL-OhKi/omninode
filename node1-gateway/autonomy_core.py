"""Phase 2.5 - confined repo workspace and deterministic verification presets.

No arbitrary shell: command.run accepts only preset names from VERIFICATION_PRESETS
and always runs with shell=False.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable, Optional

IGNORED_DIRS = frozenset({".git", "venv", ".venv", "__pycache__", ".pytest_cache", "node_modules"})
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".exe")
PROTECTED_PATHS = frozenset(
    {
        "SECURITY.md",
        "node1-gateway/policy_engine.py",
        "node1-gateway/workspace_manager.py",
    }
)
MAX_READ_BYTES = 256 * 1024
MAX_WRITE_BYTES = 1_048_576
MAX_LIST_ENTRIES = 5000
OUTPUT_LIMIT = 16000

Guard = Callable[[str, str, str], None]

_REDACTIONS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"\b(?:ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"\bpplx-[A-Za-z0-9]{16,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_TOKEN]"),
    (
        re.compile(r"(?i)\b([A-Za-z0-9_]*(?:api[_-]?key|token|secret|password|passwd)[A-Za-z0-9_]*)(\s*[=:]\s*)(['\"]?)[^\s'\"]{6,}\3"),
        r"\1\2[REDACTED]",
    ),
]


def redact(text: str) -> str:
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def is_secret_or_ignored(parts: tuple[str, ...]) -> bool:
    if not parts:
        return False
    if any(p in IGNORED_DIRS for p in parts[:-1]) or parts[-1] in IGNORED_DIRS:
        return True
    name = parts[-1].lower()
    if name.startswith(".env"):
        return True
    if name.endswith(SECRET_SUFFIXES) or name.endswith(".db") or ".sqlite" in name:
        return True
    return any(p in {".ssh", "secrets"} for p in parts)


def _trunc(text: str) -> str:
    return text if len(text) <= OUTPUT_LIMIT else text[:OUTPUT_LIMIT]


class RepoWorkspace:
    """Confined access to the repository root with snapshot-based rollback."""

    def __init__(self, root: str | os.PathLike, guard: Optional[Guard] = None, snapshot_dir: Optional[str] = None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError("workspace root does not exist")
        self.guard = guard
        self._snap_root = Path(snapshot_dir) if snapshot_dir else Path(tempfile.mkdtemp(prefix="omninode-snap-"))
        self._snap_root.mkdir(parents=True, exist_ok=True)
        self._snapshots: dict[str, Optional[Path]] = {}

    def _check(self, capability: str, resource: str, action: str) -> None:
        if self.guard is not None:
            self.guard(capability, resource, action)

    def _resolve(self, relative_path: str) -> tuple[Path, str]:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("path is required")
        if "\x00" in relative_path:
            raise PermissionError("invalid path")
        if relative_path.startswith(("/", "\\")) or PureWindowsPath(relative_path).is_absolute() or PurePosixPath(relative_path).is_absolute():
            raise PermissionError("absolute paths denied")
        parts = [p for p in re.split(r"[\\/]+", relative_path) if p not in ("", ".")]
        if not parts or ".." in parts:
            raise PermissionError("path traversal denied")
        current = self.root
        for part in parts:
            current = current / part
            if current.is_symlink():
                raise PermissionError("symlinks denied")
        resolved = current.resolve()
        if not resolved.is_relative_to(self.root):
            raise PermissionError("workspace escape denied")
        rel_parts = resolved.relative_to(self.root).parts
        if is_secret_or_ignored(rel_parts):
            raise PermissionError("sensitive or ignored path denied")
        return resolved, "/".join(rel_parts)

    @staticmethod
    def is_protected(rel_posix: str) -> bool:
        low = rel_posix.lower()
        return any(low == p.lower() for p in PROTECTED_PATHS)

    def list(self, subpath: str = "") -> dict[str, Any]:
        base = self.root
        if subpath:
            base, _ = self._resolve(subpath)
        self._check("workspace.list", str(base), "read")
        entries: list[dict[str, Any]] = []
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS and not (Path(dirpath) / d).is_symlink())
            for fname in sorted(filenames):
                full = Path(dirpath) / fname
                if full.is_symlink():
                    continue
                rel_parts = full.relative_to(self.root).parts
                if is_secret_or_ignored(rel_parts):
                    continue
                rel = "/".join(rel_parts)
                entries.append({"path": rel, "size_bytes": full.stat().st_size, "protected": self.is_protected(rel)})
                if len(entries) >= MAX_LIST_ENTRIES:
                    return {"files": entries, "truncated": True}
        return {"files": entries, "truncated": False}

    def read(self, relative_path: str) -> dict[str, Any]:
        target, rel = self._resolve(relative_path)
        self._check("workspace.read", str(target), "read")
        if not target.is_file():
            raise FileNotFoundError(rel)
        size = target.stat().st_size
        if size > MAX_READ_BYTES:
            raise ValueError("file exceeds MAX_READ_BYTES")
        raw = target.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("file is not UTF-8 text") from exc
        return {"path": rel, "size_bytes": size, "sha256": hashlib.sha256(raw).hexdigest(), "content": redact(text)}

    def write(self, relative_path: str, content: str) -> dict[str, Any]:
        target, rel = self._resolve(relative_path)
        if self.is_protected(rel):
            raise PermissionError(f"protected path: {rel}")
        if not isinstance(content, str):
            raise ValueError("content must be text")
        data = content.encode("utf-8")
        if len(data) > MAX_WRITE_BYTES:
            raise ValueError("content exceeds limit")
        self._check("workspace.write", str(target), "write")
        if target.exists() and not target.is_file():
            raise ValueError("target is not a file")
        self._snapshot(rel, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".omninode-write-", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, target)
        finally:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
        return {"path": rel, "bytes_written": len(data), "sha256": hashlib.sha256(data).hexdigest(), "created": self._snapshots[rel] is None}

    def _snapshot(self, rel: str, target: Path) -> None:
        if rel in self._snapshots:
            return
        if target.exists():
            backup = self._snap_root / hashlib.sha256(rel.encode()).hexdigest()
            shutil.copy2(target, backup)
            self._snapshots[rel] = backup
        else:
            self._snapshots[rel] = None

    def rollback(self, relative_path: str) -> dict[str, Any]:
        target, rel = self._resolve(relative_path)
        if rel not in self._snapshots:
            raise KeyError(f"no snapshot for {rel}")
        self._check("workspace.rollback", str(target), "write")
        backup = self._snapshots.pop(rel)
        if backup is None:
            try:
                target.unlink()
            except FileNotFoundError:
                pass
            action = "deleted"
        else:
            fd, tmp = tempfile.mkstemp(prefix=".omninode-rb-", dir=str(target.parent))
            os.close(fd)
            try:
                shutil.copy2(backup, tmp)
                os.replace(tmp, target)
            finally:
                try:
                    os.unlink(tmp)
                except FileNotFoundError:
                    pass
            backup.unlink(missing_ok=True)
            action = "restored"
        return {"path": rel, "action": action}

    def rollback_all(self) -> list[dict[str, Any]]:
        return [self.rollback(rel) for rel in list(self._snapshots)]

    def commit(self) -> list[str]:
        changed = sorted(self._snapshots)
        for backup in self._snapshots.values():
            if backup is not None:
                backup.unlink(missing_ok=True)
        self._snapshots.clear()
        return changed

    def pending_changes(self) -> list[str]:
        return sorted(self._snapshots)


def _py() -> str:
    return sys.executable or "python"


VERIFICATION_PRESETS: dict[str, tuple[str, tuple[str, ...]]] = {
    "python_compile": ("node1-gateway", ("{python}", "-m", "compileall", "-q", ".")),
    "python_tests": ("node1-gateway", ("{python}", "-m", "pytest", "-q")),
    "go_vet": ("omniclient", ("go", "vet", "./...")),
    "go_tests": ("omniclient", ("go", "test", "./...")),
    "git_diff_check": ("", ("git", "diff", "--check")),
}
VERIFY_ALL_ORDER = ("python_compile", "python_tests", "go_vet", "go_tests", "git_diff_check")
_SENSITIVE_ENV = re.compile(r"(?i)(key|token|secret|password|passwd|credential)")


class VerificationExecutor:
    """command.run: static presets only, shell=False, fixed cwd, bounded output."""

    def __init__(self, root: str | os.PathLike, guard: Optional[Guard] = None, audit: Any = None,
                 agent_id: str = "autonomy-agent", goal_id: str = "goal-local",
                 timeout_seconds: int = 300, presets: Optional[dict] = None):
        self.root = Path(root).resolve()
        self.guard = guard
        self.audit = audit
        self.agent_id = agent_id
        self.goal_id = goal_id
        self.timeout = timeout_seconds
        self.presets = presets if presets is not None else VERIFICATION_PRESETS

    def _log(self, decision: str, reason: str, resource: str) -> None:
        if self.audit is not None:
            self.audit.log_decision(decision, reason, self.agent_id, self.goal_id, resource, "command.run")

    def _env(self) -> dict[str, str]:
        return {k: v for k, v in os.environ.items() if not _SENSITIVE_ENV.search(k)}

    def run(self, preset: str) -> dict[str, Any]:
        if preset == "verify_all":
            return self.verify_all()
        if not isinstance(preset, str) or preset not in self.presets:
            self._log("deny", "preset_not_allowlisted", str(preset))
            raise ValueError(f"preset not allowlisted: {preset!r}")
        subdir, template = self.presets[preset]
        cwd = (self.root / subdir).resolve() if subdir else self.root
        if not cwd.is_relative_to(self.root) or not cwd.is_dir():
            self._log("deny", "cwd_unavailable", str(cwd))
            return self._result(preset, 2, 0, "", f"cwd not available: {subdir or '.'}", "error")
        try:
            if self.guard is not None:
                self.guard("command.run", str(cwd), "execute")
        except PermissionError:
            self._log("deny", "policy_denied", preset)
            raise
        argv = [a.replace("{python}", _py()) for a in template]
        if argv[0] in ("go", "git"):
            exe = shutil.which(argv[0])
            if exe is None:
                self._log("allow", "tool_not_found", preset)
                return self._result(preset, 127, 0, "", f"{argv[0]} not found in PATH", "error")
            argv[0] = exe
        self._log("allow", "preset_allowlisted", preset)
        start = time.monotonic()
        try:
            proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, shell=False,
                                  timeout=self.timeout, env=self._env())
            ms = int((time.monotonic() - start) * 1000)
            return self._result(preset, proc.returncode, ms, proc.stdout, proc.stderr, "completed")
        except subprocess.TimeoutExpired as exc:
            ms = int((time.monotonic() - start) * 1000)
            out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return self._result(preset, 124, ms, out, "timeout", "timeout")

    @staticmethod
    def _result(preset: str, code: int, ms: int, out: str, err: str, status: str) -> dict[str, Any]:
        return {"preset": preset, "status": status, "passed": code == 0, "exit_code": code,
                "duration_ms": ms, "stdout": _trunc(out or ""), "stderr": _trunc(err or "")}

    def verify_all(self) -> dict[str, Any]:
        order = [p for p in VERIFY_ALL_ORDER if p in self.presets]
        steps: list[dict[str, Any]] = []
        start = time.monotonic()
        exit_code = 0
        for name in order:
            step = self.run(name)
            steps.append(step)
            if not step["passed"]:
                exit_code = step["exit_code"] or 1
                break
        ms = int((time.monotonic() - start) * 1000)
        last = steps[-1] if steps else {"stdout": "", "stderr": ""}
        return {"preset": "verify_all", "all_passed": bool(steps) and exit_code == 0 and len(steps) == len(order),
                "passed": bool(steps) and exit_code == 0, "exit_code": exit_code, "duration_ms": ms,
                "stdout": last["stdout"], "stderr": last["stderr"], "steps": steps}
