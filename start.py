#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Monitor - 一键启动脚本
"""

import subprocess
import socket
import sys
import re
import os
import time
import threading
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        if is_port_free(port):
            return port
    return None


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def is_our_backend_ready(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


def update_env_port(env_file: Path, new_port: int):
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        if re.search(r'^PORT=', content, flags=re.MULTILINE):
            content = re.sub(r'^PORT=\d+', f'PORT={new_port}', content, flags=re.MULTILINE)
        else:
            content += f'\nPORT={new_port}'
        env_file.write_text(content, encoding='utf-8')


def update_env_frontend(env_file: Path, backend_port: int):
    new_url = f'VITE_API_BASE_URL=http://localhost:{backend_port}'
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        content = re.sub(r'^VITE_API_BASE_URL=.*', new_url, content, flags=re.MULTILINE)
    else:
        content = new_url + '\n'
    env_file.write_text(content, encoding='utf-8')


def get_python_executable() -> str:
    """优先使用 backend/venv 里的 Python，确保依赖可用"""
    venv_win = BACKEND_DIR / 'venv' / 'Scripts' / 'python.exe'
    venv_unix = BACKEND_DIR / 'venv' / 'bin' / 'python'
    if venv_win.exists():
        return str(venv_win)
    if venv_unix.exists():
        return str(venv_unix)
    return sys.executable


def check_node():
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True, shell=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_npm_deps():
    return (FRONTEND_DIR / 'node_modules').exists()


def stream_output(proc, prefix):
    try:
        for line in iter(proc.stdout.readline, b''):
            text = line.decode('utf-8', errors='replace').rstrip()
            if text:
                print(f"[{prefix}] {text}", flush=True)
    except Exception:
        pass


# ── 端口分配 ──────────────────────────────────────────────
print("TikTok Monitor starting...")
print("-" * 45)

backend_port = find_available_port(8000)
if not backend_port:
    print("ERROR: no available port in range 8000-8009")
    sys.exit(1)

frontend_port = find_available_port(5173)
if not frontend_port:
    print("ERROR: no available port in range 5173-5182")
    sys.exit(1)

if backend_port != 8000:
    print(f"[warn] port 8000 in use, backend -> {backend_port}")
if frontend_port != 5173:
    print(f"[warn] port 5173 in use, frontend -> {frontend_port}")

update_env_port(BACKEND_DIR / '.env', backend_port)
update_env_frontend(FRONTEND_DIR / '.env', backend_port)

# ── 检查 Node / npm 依赖 ──────────────────────────────────
if not check_node():
    print("ERROR: Node.js not found. Install from https://nodejs.org/")
    sys.exit(1)

if not check_npm_deps():
    print("Installing frontend dependencies...")
    result = subprocess.run('npm install', cwd=FRONTEND_DIR, shell=True)
    if result.returncode != 0:
        print("ERROR: npm install failed. Run manually: cd frontend && npm install")
        sys.exit(1)
    print("Frontend dependencies installed.")

# ── 启动后端 ──────────────────────────────────────────────
python_exec = get_python_executable()
print(f"\nStarting backend on port {backend_port}...")
print(f"Using Python: {python_exec}")

child_env = os.environ.copy()
child_env['PYTHONIOENCODING'] = 'utf-8'
child_env['PORT'] = str(backend_port)

backend_proc = subprocess.Popen(
    [python_exec, 'run.py'],
    cwd=BACKEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    env=child_env
)

threading.Thread(target=stream_output, args=(backend_proc, 'backend'), daemon=True).start()

print("Waiting for backend...")
for _ in range(30):
    time.sleep(1)
    if is_our_backend_ready(backend_port):
        print(f"Backend ready on port {backend_port}")
        break
else:
    print("ERROR: backend startup timeout. Check if dependencies are installed:")
    print(f"  cd backend && {python_exec} -m pip install -r requirements.txt")
    backend_proc.terminate()
    sys.exit(1)

# ── 启动前端 ──────────────────────────────────────────────
print(f"\nStarting frontend on port {frontend_port}...")

frontend_proc = subprocess.Popen(
    f'npm run dev -- --port {frontend_port}',
    cwd=FRONTEND_DIR,
    shell=True
)

print("Waiting for frontend...")
for _ in range(60):
    time.sleep(1)
    if is_port_in_use(frontend_port):
        print(f"Frontend ready on port {frontend_port}")
        break
else:
    print("Frontend port check timeout, it may still be starting...")

# ── 完成 ──────────────────────────────────────────────────
print()
print("-" * 45)
print(f"All services started!")
print(f"  Frontend : http://localhost:{frontend_port}")
print(f"  Backend  : http://localhost:{backend_port}")
print(f"  API Docs : http://localhost:{backend_port}/docs")
print("-" * 45)
print("Press Ctrl+C to stop all services\n")

time.sleep(1)
webbrowser.open(f"http://localhost:{frontend_port}")

try:
    backend_proc.wait()
except KeyboardInterrupt:
    print("\nStopping services...")
    backend_proc.terminate()
    frontend_proc.terminate()
    print("Stopped.")
