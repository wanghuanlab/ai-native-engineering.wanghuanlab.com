"""基线 Git 来源：必须是团队可访问的地址，并固定到标签或提交。"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


SHA = re.compile(r"^[0-9a-fA-F]{7,64}$")


def classify_source(value: str) -> str:
    """返回 ``git`` 或 ``local``。本机目录、相对路径和盘符路径都是 local。"""
    text = value.strip().strip('"').strip("'")
    if not text:
        return "local"
    if text.startswith(("git+", "git@", "git://", "gh:", "gl:")):
        return "git"
    if re.match(r"^(https?|ssh|file)://", text):
        return "git"
    if re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith("\\\\"):
        return "local"
    normalized = text.replace("\\", "/")
    if normalized.startswith(("/", "./", "../")):
        return "local"
    try:
        if Path(text).expanduser().exists():
            return "local"
    except OSError:
        return "local"
    return "local"


def sanitize_git_url(url: str) -> str:
    """去掉 https URL 里的用户名和令牌，避免写进项目的 answers 文件。"""
    if "://" not in url:
        return url
    parts = urlsplit(url)
    if parts.username is None and parts.password is None:
        return url
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))


def source_problem(value: str) -> str | None:
    if classify_source(value) == "git":
        return None
    return (
        f"基线来源是本机路径，其他机器无法用它同步：{value}\n"
        "  请改用团队可访问的 Git 地址，例如：\n"
        "    --source git@github.com:org/ai-native-engineering.git\n"
        "  或设置环境变量 BASELINE_SOURCE。"
    )


def git_remote_url(url: str) -> str:
    """给 git 命令用的地址。Copier 接受 git+file://，git 本身不接受 git+ 前缀。"""
    if url.startswith("git+"):
        return url[4:]
    return url


def _git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git_stdout(repo: Path, *args: str) -> str:
    result = _git(["git", *args], cwd=repo)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def default_source(repo: Path) -> str:
    url = git_stdout(repo, "remote", "get-url", "origin")
    if not url:
        raise SystemExit(
            "基线仓库没有 origin 远端。请用 --source 或环境变量 BASELINE_SOURCE 指定团队可访问的 Git 地址。"
        )
    cleaned = sanitize_git_url(url)
    problem = source_problem(cleaned)
    if problem:
        raise SystemExit(
            f"origin 不能作为基线来源。\n{problem}"
        )
    if cleaned != url:
        print("已去掉 origin 地址中的凭据，避免写入项目。", file=sys.stderr)
    return cleaned


def default_ref(repo: Path) -> str:
    tag = git_stdout(repo, "describe", "--tags", "--exact-match")
    if tag:
        return tag
    sha = git_stdout(repo, "rev-parse", "HEAD")
    if not sha:
        raise SystemExit("无法确定当前提交。请用 --ref 指定已发布的标签。")
    print(
        f"! 当前提交没有标签，已固定为提交 {sha}。该提交必须已经在基线远端上。",
        file=sys.stderr,
    )
    return sha


def ref_exists(url: str, ref: str) -> bool:
    remote = git_remote_url(url)
    if SHA.fullmatch(ref):
        listing = _git(["git", "ls-remote", remote])
        if listing.returncode != 0:
            return False
        prefix = ref.lower()
        for line in listing.stdout.splitlines():
            fields = line.split()
            if not fields:
                continue
            sha = fields[0].lower()
            if sha == prefix or sha.startswith(prefix):
                return True
        return False
    candidates = [f"refs/tags/{ref}", f"refs/heads/{ref}", ref]
    for candidate in candidates:
        result = _git(["git", "ls-remote", remote, candidate])
        if result.returncode == 0 and result.stdout.strip():
            return True
    return False


def reachability_problem(url: str, ref: str) -> str | None:
    remote = git_remote_url(url)
    probe = _git(["git", "ls-remote", remote])
    if probe.returncode != 0:
        detail = (probe.stderr or probe.stdout or "").strip()
        lines = [f"✗ 无法访问基线来源 {url}"]
        if detail:
            lines.append(f"  {detail.splitlines()[-1]}")
        lines.append("  请确认团队网络能访问该地址，或用 --source 指定其他 Git 地址。")
        return "\n".join(lines)
    if not ref_exists(url, ref):
        return f"✗ 基线来源 {url} 上找不到引用 {ref}。请确认标签或分支已推送。"
    return None


def copier_command() -> list[str]:
    found = shutil.which("copier")
    if found:
        return [found]
    if importlib.util.find_spec("copier") is not None:
        return [sys.executable, "-m", "copier"]
    if shutil.which("uvx"):
        return ["uvx", "copier"]
    if shutil.which("pipx"):
        return ["pipx", "run", "copier"]
    raise SystemExit("未找到 copier。请先安装：pip install copier，或安装 uv 后使用 uvx。")


def read_src_path(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("_src_path:"):
            raw = line.split(":", 1)[1].strip()
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
                raw = raw[1:-1]
            return raw
    return None


def yaml_double(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_src_path(path: Path, source: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    found = False
    rewritten: list[str] = []
    for line in lines:
        if line.startswith("_src_path:"):
            newline = "\r\n" if line.endswith("\r\n") else "\n"
            rewritten.append(f"_src_path: {yaml_double(source)}{newline}")
            found = True
        else:
            rewritten.append(line if line.endswith(("\n", "\r\n")) else line)
    if not found:
        raise SystemExit(f"✗ {path} 缺少 _src_path，无法确定基线来源。")
    path.write_bytes("".join(rewritten).encode("utf-8"))


def resolve_create_source(repo: Path, source_flag: str | None) -> str:
    chosen = source_flag or os.environ.get("BASELINE_SOURCE") or ""
    if not chosen:
        return default_source(repo)
    cleaned = sanitize_git_url(chosen.strip())
    if cleaned != chosen.strip():
        print("已去掉 --source / BASELINE_SOURCE 中的凭据。", file=sys.stderr)
    problem = source_problem(cleaned)
    if problem:
        raise SystemExit(problem)
    return cleaned


def resolve_create_ref(repo: Path, ref_flag: str | None) -> str:
    chosen = ref_flag or os.environ.get("BASELINE_REF") or ""
    if chosen:
        return chosen
    return default_ref(repo)
