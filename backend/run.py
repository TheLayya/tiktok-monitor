import uvicorn
import socket
import sys
import re
import os
from pathlib import Path
from app.core.config import settings


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    return None


def update_env_port(new_port: int):
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        content = re.sub(r'^PORT=\d+', f'PORT={new_port}', content, flags=re.MULTILINE)
        env_file.write_text(content, encoding='utf-8')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', settings.PORT))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', port)) == 0:
            print(f"[warn] port {port} in use, finding available port...")
            available_port = find_available_port(port + 1)
            if available_port:
                port = available_port
                update_env_port(port)
                print(f"[info] using port {port}")
            else:
                print(f"[error] no available port found ({port}-{port+9})")
                sys.exit(1)

    uvicorn.run("app.main:app", host=settings.HOST, port=port, reload=False)
