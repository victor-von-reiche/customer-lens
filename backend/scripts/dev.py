"""Install local dependencies and run both development servers."""

import argparse
import hashlib
import os
import signal
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def install_if_changed(command, cwd, inputs, stamp):
    """Install dependencies only when their specification has changed."""
    digest = hashlib.sha256(
        b"".join(p.read_bytes() for p in inputs)
    ).hexdigest()
    if not stamp.exists() or stamp.read_text() != digest:
        subprocess.run(command, cwd=cwd, check=True)
        stamp.write_text(digest)


def main():
    """Start live mode unless the keyless demo is explicitly selected."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true")
    mode.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("Python 3.12 or newer is required; Python 3.12 is tested")
    backend = ROOT / "backend"
    frontend = ROOT / "frontend"
    environment = backend / ".venv"
    python = environment / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    if not python.exists():
        venv.create(environment, with_pip=True)
    install_if_changed(
        [str(python), "-m", "pip", "install", "-r", "requirements.txt"],
        backend,
        [backend / "requirements.txt"],
        environment / ".dependencies",
    )
    install_if_changed(
        ["npm", "ci"],
        frontend,
        [frontend / "package-lock.json"],
        frontend / "node_modules/.dependencies",
    )
    env = {**os.environ, "APP_MODE": "demo" if args.demo else "live"}
    commands = [
        (
            [
                str(python),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            backend,
        ),
        (["npm", "run", "dev"], frontend),
    ]
    children = []
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        for command, cwd in commands:
            children.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    start_new_session=os.name != "nt",
                )
            )
        print("CustomerLens: http://127.0.0.1:5173", flush=True)
        while True:
            for process in children:
                try:
                    code = process.wait(timeout=0.5)
                    raise SystemExit(code or 1)
                except subprocess.TimeoutExpired:
                    pass
    except KeyboardInterrupt:
        pass
    finally:
        for process in children:
            try:
                if os.name == "nt":
                    process.terminate()
                else:
                    os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for process in children:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
