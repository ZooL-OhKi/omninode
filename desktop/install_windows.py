"""Per-user Chrome/Edge native host setup. Dry-run unless --apply."""
import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import venv


def checked_path(value):
    text = str(value)
    path = PureWindowsPath(text)
    if (not path.is_absolute() or path.drive.startswith("\\") or ".." in path.parts
            or any(ord(c) < 32 or ord(c) > 126 or c in '"%!^&|<>' for c in text)):
        raise ValueError("use an absolute local path without CMD metacharacters")
    return str(path)


def build_plan(source, base, extension_id, browser="chrome"):
    if not re.fullmatch(r"[a-p]{32}", extension_id or ""):
        raise ValueError("invalid extension ID")
    if browser not in {"chrome", "edge"}:
        raise ValueError("unsupported browser")
    source, base = checked_path(source), checked_path(base)
    origin = "chrome-extension://" + extension_id + "/"
    root = PureWindowsPath(base)
    python = str(root / "runtime" / "Scripts" / "python.exe")
    host = str(PureWindowsPath(source) / "native_host.py")
    manifest_path = str(root / "com.omninode.desktop.json")
    vendor = "Google\\Chrome" if browser == "chrome" else "Microsoft\\Edge"
    registry = "Software\\" + vendor + "\\NativeMessagingHosts\\com.omninode.desktop"
    launcher = '@echo off\r\nsetlocal\r\nset "OMNINODE_NATIVE_ORIGIN=' + origin + '"\r\n"' + python + '" -u "' + host + '" %*\r\n'
    return {"source": source, "base": base, "origin": origin, "browser": browser,
            "python": python, "manifest_path": manifest_path, "registry": registry,
            "launcher": launcher,
            "manifest": {"name": "com.omninode.desktop", "description": "OmniNode local desktop host",
                         "path": str(root / "host.cmd"), "type": "stdio", "allowed_origins": [origin]}}


def reject_links(path):
    for item in [path, *path.parents]:
        if item.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(item)):
            raise ValueError("setup refuses linked or junction paths")


def apply_plan(plan):
    if sys.platform != "win32":
        raise RuntimeError("installation supports Windows only")
    import winreg
    base = Path(plan["base"])
    source = Path(plan["source"])
    reject_links(base)
    reject_links(source)
    if not (source / "native_host.py").is_file() or not (source / "requirements-windows.txt").is_file():
        raise FileNotFoundError("native host source or requirements missing")
    identity = {key: plan[key] for key in ("source", "origin", "browser")}
    marker = base / "managed.json"
    reject_links(marker)
    reject_links(source / "native_host.py")
    reject_links(source / "requirements-windows.txt")
    if base.exists():
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != identity:
            raise FileExistsError("existing setup directory is not owned by this pairing")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, plan["registry"]) as key:
            existing, _ = winreg.QueryValueEx(key, "")
            if existing != plan["manifest_path"]:
                raise FileExistsError("native registration already points elsewhere")
    except FileNotFoundError:
        pass
    base.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(identity), encoding="utf-8")
    runtime = base / "runtime"
    reject_links(runtime)
    venv.EnvBuilder(with_pip=True).create(runtime)
    subprocess.run([plan["python"], "-m", "pip", "install", "--disable-pip-version-check",
                    "-r", str(source / "requirements-windows.txt")], check=True)
    for file in [base / "host.cmd", marker, Path(plan["manifest_path"])]:
        reject_links(file)
    (base / "host.cmd").write_bytes(plan["launcher"].encode("utf-8"))
    Path(plan["manifest_path"]).write_text(json.dumps(plan["manifest"], indent=2), encoding="utf-8")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, plan["registry"]) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, plan["manifest_path"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extension-id", required=True)
    parser.add_argument("--browser", choices=["chrome", "edge"], default="chrome")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA is required")
    plan = build_plan(Path(__file__).resolve().parent,
                      PureWindowsPath(local) / "OmniNode" / ("NativeHost-" + args.browser),
                      args.extension_id, args.browser)
    if args.apply:
        apply_plan(plan)
        print("Native host registered for this user; desktop remains off until local consent.")
    else:
        print(json.dumps({"dry_run": True, "plan": plan}, indent=2))


if __name__ == "__main__":
    main()
