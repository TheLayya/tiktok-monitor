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
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"


def is_port_free(port: int) -> bool:
    """检查端口是否完全空闲（没有任何进程监听）"""
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


def is_our_backend_ready(port: int) -> bool:
    """通过 /health 接口确认是我们的后端在运行"""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def update_env_port(env_file: Path, new_port: int):
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        if re.search(r'^PORT=', content, flags=re.MULTILINE):
            content = re.sub(r'^PORT=\d+', f'PORT={new_port}', content, flags=re.MULTILINE)
        else:
            content += f'\nPORT={new_port}'
        env_file.write_text(content, encoding='utf-8')


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

# 写入 backend/.env，vite.config.js 启动时会读取
update_env_port(BACKEND_DIR / '.env', backend_port)

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

# ── 公共环境变量 ──────────────────────────────────────────
child_env = os.environ.copy()
child_env['PYTHONIOENCODING'] = 'utf-8'
child_env['PORT'] = str(backend_port)

# ── 启动后端 ──────────────────────────────────────────────
print(f"\nStarting backend on port {backend_port}...")

backend_proc = subprocess.Popen(
    [sys.executable, 'run.py'],
    cwd=BACKEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    env=child_env
)

threading.Thread(target=stream_output, args=(backend_proc, 'backend'), daemon=True).start()

# 用 /health 接口确认后端就绪，避免误判其他进程占用的端口
print("Waiting for backend...")
for _ in range(30):
    time.sleep(1)
    if is_our_backend_ready(backend_port):
        print(f"Backend ready on port {backend_port}")
        break
else:
    print("ERROR: backend startup timeout")
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
