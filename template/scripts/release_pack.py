#!/usr/bin/env python3
"""生成交付包。版本标签必须指向当前提交。--images 需要 Docker Buildx。"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from lib.proc import IS_WINDOWS, configure_stdio, run


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("用法：release-pack <版本，如 v1.3.0> [--images]", file=sys.stderr)
        return 2
    version = args[0]
    with_images = "--images" in args[1:]
    if not VERSION_RE.match(version):
        print("版本格式应为 vMAJOR.MINOR.PATCH", file=sys.stderr)
        return 1
    project = json.loads((ROOT / ".baseline" / "project.json").read_text(encoding="utf-8"))
    code = project["projectCode"]
    dialects = project["dialects"]
    docs = ROOT / "docs" / "releases" / version
    out = ROOT / "dist" / f"{code}-{version}"
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        print("工作区有未提交的改动", file=sys.stderr)
        return 1
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    tagged = subprocess.run(["git", "rev-parse", f"{version}^{{commit}}"], cwd=ROOT, capture_output=True, text=True)
    if tagged.returncode != 0 or tagged.stdout.strip() != head.stdout.strip():
        print(f"请先在当前提交上打标签：git tag -a {version} -m {version}", file=sys.stderr)
        return 1
    for name in ("release-notes.md", "deploy-guide.md", "upgrade-guide.md"):
        if not (docs / name).is_file():
            print(f"缺少 docs/releases/{version}/{name}（模板见 docs/_templates/）", file=sys.stderr)
            return 1

    if out.exists():
        shutil.rmtree(out)
    for folder in ("app", "db", "config"):
        (out / folder).mkdir(parents=True)
    from lib.proc import maven_argv

    run(maven_argv(["package", "-DskipTests"], windows=IS_WINDOWS), cwd=ROOT / "backend")
    env = os.environ.copy()
    env["CI"] = "true"
    run(["pnpm", "-s", "gen:api"], cwd=ROOT / "frontend", env=env)
    run(["pnpm", "-s", "build"], cwd=ROOT / "frontend", env=env)
    shutil.copy2(ROOT / "backend" / "app" / "target" / f"{code}-app.jar", out / "app")
    shutil.copytree(ROOT / "frontend" / "apps" / "admin" / "dist", out / "app" / "admin")
    screen = ROOT / "frontend" / "apps" / "screen" / "dist"
    if screen.is_dir():
        shutil.copytree(screen, out / "app" / "screen")
    for dialect in dialects:
        target = out / "db" / dialect
        target.mkdir(parents=True, exist_ok=True)
        source = ROOT / "db" / "migration" / dialect
        if source.is_dir():
            for sql in source.glob("V*.sql"):
                shutil.copy2(sql, target / sql.name)
    config = ROOT / "backend" / "app" / "src" / "main" / "resources"
    for yml in config.glob("application*.yml"):
        shutil.copy2(yml, out / "config" / yml.name)
    for doc in docs.glob("*.md"):
        shutil.copy2(doc, out / doc.name)
    if with_images:
        image_dir = out / "images"
        image_dir.mkdir(parents=True)
        for arch in ("amd64", "arm64"):
            for service in ("backend", "frontend"):
                destination = image_dir / f"{code}-{service}-{version}-{arch}.tar"
                run(
                    [
                        "docker", "buildx", "build", "--platform", f"linux/{arch}",
                        "-f", f"deploy/docker/{service}.Dockerfile",
                        "-t", f"{code}-{service}:{version}",
                        "--output", f"type=docker,dest={destination}", ".",
                    ],
                    cwd=ROOT,
                )
    write_checksums(out)
    archive = ROOT / "dist" / f"{code}-{version}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(out, arcname=out.name)
    print(f"交付包：dist/{code}-{version}.tar.gz")
    return 0


def write_checksums(out: Path) -> None:
    paths = [path for path in out.rglob("*") if path.is_file() and path.name != "checksums.txt"]
    relative = sorted((path.relative_to(out).as_posix() for path in paths), key=lambda item: item.encode())
    lines = []
    for name in relative:
        digest = hashlib.sha256((out / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  ./{name}")
    (out / "checksums.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


if __name__ == "__main__":
    from lib.proc import CommandFailed

    try:
        sys.exit(main())
    except CommandFailed as exc:
        sys.exit(exc.returncode or 1)
