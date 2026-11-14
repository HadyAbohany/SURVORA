"""Start a loopback Uvicorn server and run the offline smoke test."""
import os
import socket
import subprocess
import sys
import time

import httpx

from scripts import smoke_http


def main():
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    start = time.perf_counter()
    env = dict(os.environ)
    env.update({name: '' for name in ['GEMINI_API_KEY', *[f'GEMINI_API_KEY_{i}' for i in range(1, 11)]]})
    env.update(NOVA_ENABLE_SEMANTIC='false', NOVA_CLIENT_TOKEN='')
    server = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', str(port), '--log-level', 'error'],
        env=env,
    )
    try:
        smoke_http.BASE = f'http://127.0.0.1:{port}'
        smoke_http.TOKEN = ''
        with httpx.Client(base_url=smoke_http.BASE, timeout=.25, trust_env=False) as client:
            while time.perf_counter() - start < 8 and server.poll() is None:
                try:
                    if client.get('/health').status_code == 200:
                        break
                except httpx.TransportError:
                    time.sleep(.025)
            else:
                raise RuntimeError('NOVA did not become healthy on loopback')
        print(f'Start to first health: {(time.perf_counter() - start) * 1000:.1f}ms')
        smoke_http.main()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == '__main__':
    main()
