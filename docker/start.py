"""Arranca Astro y FastAPI como un servicio de contenedor supervisado."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time


processes: list[subprocess.Popen] = []


def stop_services(*_args):
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("Node.js is required to serve the Astro application.", file=sys.stderr)
        return 1

    astro_cwd = "frontend" if os.path.isdir("frontend") else "blog"
    commands = [
        ([sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"], "."),
        ([node, "dist/server/entry.mjs"], astro_cwd),
    ]
    signal.signal(signal.SIGTERM, stop_services)
    signal.signal(signal.SIGINT, stop_services)
    try:
        for command, cwd in commands:
            processes.append(subprocess.Popen(command, cwd=cwd, env=os.environ.copy()))
        while True:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    return exit_code
            time.sleep(0.25)
    finally:
        stop_services()


if __name__ == "__main__":
    raise SystemExit(main())
