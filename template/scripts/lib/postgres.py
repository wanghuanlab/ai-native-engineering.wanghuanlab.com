"""临时 PostgreSQL 容器。db-schema 与升级路径测试共用。需要本机 Docker。"""
from __future__ import annotations

import os
import random
import subprocess
import time
from pathlib import Path


class Postgres:
    def __init__(self, image: str | None = None) -> None:
        self.image = image or os.environ.get("PG_IMAGE") or "postgres:17-alpine"
        self.container = f"baseline-pg-{os.getpid()}-{random.randint(0, 32767)}"

    def start(self) -> None:
        if subprocess.run(["docker", "version"], capture_output=True).returncode != 0:
            raise SystemExit("需要 Docker。Windows 请安装 Docker Desktop；没有它就无法在本机执行迁移。")
        subprocess.run(
            [
                "docker", "run", "-d", "--rm", "--name", self.container,
                "-e", "POSTGRES_PASSWORD=postgres", "-e", "POSTGRES_DB=app", self.image,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        ok = 0
        for _ in range(60):
            probe = subprocess.run(
                ["docker", "exec", self.container, "psql", "-U", "postgres", "-d", "app", "-qtAc", "select 1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if probe.returncode == 0:
                ok += 1
                if ok >= 2:
                    return
            else:
                ok = 0
            time.sleep(1)
        self.stop()
        raise SystemExit("PostgreSQL 容器启动超时")

    def stop(self) -> None:
        subprocess.run(
            ["docker", "rm", "-f", self.container],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def reset(self) -> None:
        subprocess.run(
            [
                "docker", "exec", self.container, "psql", "-U", "postgres", "-d", "app", "-qc",
                "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def execute(self, sql: bytes | str) -> None:
        data = sql if isinstance(sql, bytes) else sql.encode("utf-8")
        result = subprocess.run(
            [
                "docker", "exec", "-i", self.container, "psql", "-U", "postgres", "-d", "app",
                "-q", "-v", "ON_ERROR_STOP=1",
            ],
            input=data,
            stdout=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    def execute_file(self, path: Path) -> None:
        self.execute(path.read_bytes())

    def query(self, sql: str) -> str:
        result = subprocess.run(
            [
                "docker", "exec", self.container, "psql", "-U", "postgres", "-d", "app",
                "-qtA", "-F", "\t", "-c", sql,
            ],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode("utf-8")

    def __enter__(self) -> Postgres:
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()
