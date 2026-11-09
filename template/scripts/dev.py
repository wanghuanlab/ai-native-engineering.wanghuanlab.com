#!/usr/bin/env python3
"""启动本地依赖和前后端。

数据库由 compose 创建。表结构和初始数据在后端启动时由 Flyway 执行，不需要手跑 SQL。
本机 6379 已经是可用的 Redis 时直接复用，不再另起一个容器。
"""

from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ["docker", "compose", "-f", "deploy/local/compose.yaml"]


def project_code() -> str:
    answers = ROOT / ".baseline" / "copier-answers.yml"
    text = answers.read_text(encoding="utf-8")
    match = re.search(r"^project_code:\s*['\"]?([a-z][a-z0-9]+)", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"找不到项目代号：{answers}")
    return match.group(1)


def admin_username() -> str | None:
    answers = ROOT / ".baseline" / "plugins" / "admin.yml"
    if not answers.is_file():
        return None
    text = answers.read_text(encoding="utf-8")
    match = re.search(r"^initial_admin_username:\s*['\"]?([A-Za-z0-9_-]+)", text, re.MULTILINE)
    return match.group(1) if match else "admin"


def compose_has(service: str) -> bool:
    text = (ROOT / "deploy" / "local" / "compose.yaml").read_text(encoding="utf-8")
    return re.search(rf"^  {re.escape(service)}:\s*$", text, re.MULTILINE) is not None


def port_open(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def free_port(preferred: int) -> int:
    if not port_open(preferred):
        return preferred
    for port in range(preferred + 1, preferred + 30):
        if not port_open(port):
            return port
    raise SystemExit(f"从 {preferred} 起没有找到空闲端口")


def redis_probe(port: int, password: str = "") -> str:
    """返回 PONG、NOAUTH 或 FAIL。"""
    try:
        with socket.create_connection(("127.0.0.1", port), 2) as sock:
            sock.settimeout(2)
            if password:
                encoded = password.encode()
                sock.sendall(
                    b"*2\r\n$4\r\nAUTH\r\n$" + str(len(encoded)).encode() + b"\r\n" + encoded + b"\r\n"
                )
                if not sock.recv(64).startswith(b"+OK"):
                    return "FAIL"
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(64)
            if data.startswith(b"+PONG"):
                return "PONG"
            if b"NOAUTH" in data:
                return "NOAUTH"
            return "FAIL"
    except OSError:
        return "FAIL"


def container_running(name: str) -> bool:
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def compose(*args: str) -> None:
    run([*COMPOSE, *args])


def wait_until(label: str, probe, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if probe():
            return
        time.sleep(1)
    raise SystemExit(f"{label} 在 {timeout} 秒内没有就绪")


def ensure_postgres(code: str) -> None:
    name = f"{code}-postgres"
    if port_open(5432) and not container_running(name):
        raise SystemExit("本机 5432 已被其他服务占用，请先释放该端口。")
    compose("up", "-d", "postgres")
    wait_until(
        "PostgreSQL",
        lambda: subprocess.run(
            ["docker", "exec", name, "pg_isready", "-U", code, "-d", code],
            capture_output=True,
            check=False,
        ).returncode
        == 0,
    )
    print(f"✓ PostgreSQL 已就绪（localhost:5432/{code}）", flush=True)


def container_host_port(name: str) -> str | None:
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "-f",
            '{{with index .NetworkSettings.Ports "6379/tcp"}}{{(index . 0).HostPort}}{{end}}',
            name,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    port = result.stdout.strip()
    return port or None


def wait_redis(port: int, password: str = "") -> None:
    wait_until("Redis", lambda: redis_probe(port, password) == "PONG")


def ensure_redis(code: str) -> tuple[str, str] | None:
    """返回 (端口, 口令)。口令为空表示不认证。没有 Redis 服务时返回 None。"""
    if not compose_has("redis"):
        return None
    name = f"{code}-redis"
    configured = os.environ.get("REDIS_PASSWORD", "")
    if container_running(name):
        port = int(container_host_port(name) or "6379")
        wait_redis(port)
        print(f"✓ Redis 容器已就绪（127.0.0.1:{port}）", flush=True)
        return str(port), ""
    if not port_open(6379):
        compose("up", "-d", "redis")
        wait_redis(6379)
        print("✓ 已启动 Redis（127.0.0.1:6379）", flush=True)
        return "6379", ""
    if redis_probe(6379) == "PONG":
        print("✓ 复用本机 6379 上已有的 Redis", flush=True)
        return "6379", ""
    if configured and redis_probe(6379, configured) == "PONG":
        print("✓ 复用本机 6379 上需要口令的 Redis", flush=True)
        return "6379", configured
    host_port = str(free_port(6380))
    if subprocess.run(["docker", "inspect", name], capture_output=True, check=False).returncode == 0:
        run(["docker", "rm", "-f", name])
    run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            f"127.0.0.1:{host_port}:6379",
            "redis:7-alpine",
        ]
    )
    wait_redis(int(host_port))
    print(f"✓ 6379 已被占用，已在 127.0.0.1:{host_port} 启动项目 Redis", flush=True)
    return host_port, ""


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def popen(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True)


def stop(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        proc.terminate()
    else:
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)


def prepare_frontend() -> None:
    frontend = ROOT / "frontend"
    if not (frontend / "node_modules").is_dir():
        run(["pnpm", "install"], cwd=frontend)
    run(["pnpm", "-s", "gen:api"], cwd=frontend)


def start() -> int:
    code = project_code()
    ensure_postgres(code)
    redis = ensure_redis(code)
    prepare_frontend()
    api_port = free_port(8080)
    web_port = free_port(5173)
    if api_port != 8080:
        print(f"✓ 8080 已被占用，后端改用 {api_port}", flush=True)
    if web_port != 5173:
        print(f"✓ 5173 已被占用，前端改用 {web_port}", flush=True)
    env = os.environ.copy()
    env.pop("REDIS_PASSWORD", None)
    env["SERVER_PORT"] = str(api_port)
    env["API_PROXY"] = f"http://127.0.0.1:{api_port}"
    if redis:
        env["REDIS_HOST"] = "127.0.0.1"
        env["REDIS_PORT"] = redis[0]
        if redis[1]:
            env["REDIS_PASSWORD"] = redis[1]
    mvnw = ROOT / "backend" / "mvnw"
    mvnw.chmod(mvnw.stat().st_mode | 0o111)
    # 父工程也继承了 spring-boot 插件，不能把 run 目标跑在整个反应器上。
    run(["./mvnw", "-pl", "app", "-am", "-DskipTests", "install"], ROOT / "backend")
    backend = popen(["./mvnw", "-pl", "app", "spring-boot:run"], ROOT / "backend", env)
    frontend = popen(
        ["pnpm", "exec", "vite", "--host", "127.0.0.1", "--port", str(web_port), "--strictPort"],
        ROOT / "frontend" / "apps" / "admin",
        env,
    )
    username = admin_username()
    announced = False
    deadline = time.time() + 300
    try:
        while True:
            if backend.poll() is not None or frontend.poll() is not None:
                code_backend = backend.poll()
                code_frontend = frontend.poll()
                return code_backend if code_backend not in (None, 0) else code_frontend or 1
            ready = http_ok(f"http://127.0.0.1:{api_port}/actuator/health") and port_open(web_port)
            if ready and not announced:
                print(f"✓ 后端 http://localhost:{api_port}", flush=True)
                print(f"✓ 前端 http://localhost:{web_port}", flush=True)
                if username:
                    print(f"✓ 初始管理员 {username}，初始密码 Admin@123。登录后请立即修改。", flush=True)
                announced = True
            if not announced and time.time() > deadline:
                raise SystemExit("前后端在 5 分钟内没有就绪")
            time.sleep(1)
    finally:
        stop(frontend)
        stop(backend)


def main() -> int:
    try:
        return start()
    except KeyboardInterrupt:
        return 0
    except subprocess.CalledProcessError as ex:
        print(ex, file=sys.stderr)
        return ex.returncode or 1


if __name__ == "__main__":
    sys.exit(main())
