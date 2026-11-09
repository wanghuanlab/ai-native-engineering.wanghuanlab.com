#!/usr/bin/env python3
"""安装、查看和升级源码注入的插件。

  plugin.py list
  plugin.py add <名称> [--source <目录或 Git 地址>] [--ref <标签>]
  plugin.py update <名称> <版本标签>
  plugin.py add-selected
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.baseline_source import classify_source, copier_command, git_remote_url, read_src_path  # noqa: E402
from lib.proc import configure_stdio  # noqa: E402

_NESTED = object()
VARIABLE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
VERSION_LINE = re.compile(r"^V(\d{12})__")


def parse_scalar(text: str):
    if text in ("", "~", "null", "Null", "NULL"):
        return None
    if text == "[]":
        return []
    if text == "{}":
        return {}
    if text in ("true", "false"):
        return text == "true"
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        if text[0] == "'":
            return text[1:-1].replace("''", "'")
        return json.loads(text)
    return text


def split_key(text: str):
    if text.startswith(("'", '"')):
        raise SystemExit(f"插件清单不支持带引号的键：{text}")
    key, sep, rest = text.partition(":")
    if not sep:
        raise SystemExit(f"无法解析插件清单：{text}")
    rest = rest.strip()
    if rest == "":
        return key.strip(), _NESTED
    return key.strip(), parse_scalar(rest)


def logical_lines(text: str) -> list[tuple[int, str]]:
    raw = text.splitlines()
    lines: list[tuple[int, str]] = []
    index = 0
    while index < len(raw):
        line = raw[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if ": |" in stripped or stripped.endswith(": |") or stripped.endswith(": |-") or stripped.endswith(": |+"):
            key, _, marker = stripped.partition(":")
            marker = marker.strip()
            index += 1
            block: list[str] = []
            while index < len(raw):
                nxt = raw[index]
                if nxt.strip() == "":
                    block.append("")
                    index += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                if nxt_indent <= indent:
                    break
                prefix = indent + 2
                block.append(nxt[prefix:] if len(nxt) >= prefix else nxt.lstrip(" "))
                index += 1
            literal = "\n".join(block)
            if marker != "|-":
                literal += "\n"
            lines.append((indent, f"{key.strip()}: {json.dumps(literal, ensure_ascii=False)}"))
            continue
        lines.append((indent, stripped))
        index += 1
    return lines


def parse_at(lines: list[tuple[int, str]], index: int, indent: int):
    if index >= len(lines):
        return {}, index
    if lines[index][0] == indent and lines[index][1].startswith("- "):
        items = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            item_text = lines[index][1][2:].strip()
            index += 1
            if ": " in item_text or item_text.endswith(":"):
                key, value = split_key(item_text)
                mapping: dict = {}
                child_indent = indent + 2
                if value is _NESTED:
                    value, index = parse_at(lines, index, child_indent)
                mapping[key] = value
                while (
                    index < len(lines)
                    and lines[index][0] == child_indent
                    and not lines[index][1].startswith("- ")
                ):
                    child_key, child_value = split_key(lines[index][1])
                    index += 1
                    if child_value is _NESTED:
                        child_value, index = parse_at(lines, index, child_indent + 2)
                    mapping[child_key] = child_value
                items.append(mapping)
            else:
                items.append(parse_scalar(item_text))
        return items, index
    mapping = {}
    while index < len(lines) and lines[index][0] == indent and not lines[index][1].startswith("- "):
        key, value = split_key(lines[index][1])
        index += 1
        if value is _NESTED:
            value, index = parse_at(lines, index, indent + 2)
        mapping[key] = value
    return mapping, index


def parse_yaml(text: str):
    lines = logical_lines(text)
    if not lines:
        return {}
    value, index = parse_at(lines, 0, lines[0][0])
    if index != len(lines):
        raise SystemExit(f"插件清单在第 {index + 1} 项之后还有无法归位的内容")
    return value


def read_plugins(text: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("plugins:"):
            continue
        rest = line.split(":", 1)[1].strip()
        if rest == "[]" or rest in ("~", "null", ""):
            if rest == "":
                items = []
                for nxt in lines[index + 1 :]:
                    stripped = nxt.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    if stripped.startswith("- "):
                        items.append(str(parse_scalar(stripped[2:].strip())))
                        continue
                    break
                return items
            return []
        if rest.startswith("["):
            loaded = json.loads(rest)
            return [str(item) for item in loaded]
        return [str(parse_scalar(rest))]
    return []


def render(text: str, values: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"插件清单引用了未知变量 {key}")
        return values[key]

    return VARIABLE.sub(replace, text)


def project_values() -> dict[str, str]:
    project = json.loads((ROOT / ".baseline/project.json").read_text(encoding="utf-8"))
    package = project["packageName"]
    code = project["projectCode"]
    suffix = "." + code
    prefix = package[: -len(suffix)] if package.endswith(suffix) else package
    return {
        "project_code": code,
        "project_name": project["projectName"],
        "package_name": package,
        "package_path": package.replace(".", "/"),
        "package_root": prefix,
        "dialects": ",".join(project["dialects"]),
    }


def answers_text() -> str:
    path = ROOT / ".baseline/copier-answers.yml"
    if not path.is_file():
        raise SystemExit("找不到 .baseline/copier-answers.yml，请在项目根目录执行")
    return path.read_text(encoding="utf-8")


def read_commit(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("_commit:"):
            value = parse_scalar(line.split(":", 1)[1].strip())
            return None if value is None else str(value)
    return None


def version_tuple(text: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def load_catalog() -> dict:
    path = ROOT / ".baseline/plugin-catalog.yml"
    if not path.is_file():
        return {}
    data = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(".baseline/plugin-catalog.yml 格式不正确")
    return data


def baseline_root() -> Path | None:
    source = read_src_path(answers_text())
    if not source or classify_source(source) != "local":
        return None
    path = Path(source)
    return path if path.is_dir() else None


def resolve_source(name: str, source: str | None) -> str:
    if source:
        return source
    entry = load_catalog().get(name)
    if not isinstance(entry, dict):
        raise SystemExit(f"插件目录里没有 {name}。请用 --source 指定模板目录或 Git 地址。")
    root = baseline_root()
    local = str(entry.get("local") or "")
    if root and local:
        candidate = root / local
        if (candidate / "copier.yml").is_file() and (candidate / "plugin.yml").is_file():
            return str(candidate)
    git = str(entry.get("git") or "")
    if git:
        return git
    raise SystemExit(
        f"找不到插件 {name} 的模板。基线来源不是本机检出，且目录里没有填写 git 地址。\n"
        f"  请执行：scripts/plugin.sh add {name} --source <模板目录或 Git 地址>"
    )


def git_show(repo: Path, ref: str, file: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{file}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"在 {repo} 的 {ref} 上找不到 {file}。{detail}")
    return result.stdout


def clone_source(url: str, ref: str | None) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ane-plugin-"))
    command = ["git", "clone", "--quiet", "--depth", "1"]
    if ref:
        command += ["--branch", ref]
    command += [git_remote_url(url), str(tmp)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"无法获取插件模板 {url}。{detail}")
    return tmp


def read_manifest(source: str, ref: str | None) -> dict:
    path = Path(source)
    if path.is_dir():
        if ref:
            text = git_show(path, ref, "plugin.yml")
        else:
            manifest_path = path / "plugin.yml"
            if not manifest_path.is_file():
                raise SystemExit(f"{path} 缺少 plugin.yml")
            text = manifest_path.read_text(encoding="utf-8")
        data = parse_yaml(text)
    else:
        checkout = clone_source(source, ref)
        try:
            data = parse_yaml((checkout / "plugin.yml").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(checkout, ignore_errors=True)
    if not isinstance(data, dict) or "name" not in data:
        raise SystemExit(f"{source} 的 plugin.yml 缺少 name")
    return data


def ensure_baseline(manifest: dict) -> None:
    baseline = manifest.get("baseline") or {}
    if not isinstance(baseline, dict):
        return
    minimum = str(baseline.get("min") or "")
    if not minimum:
        return
    commit = read_commit(answers_text())
    got = version_tuple(commit or "")
    need = version_tuple(minimum)
    if got is None or need is None:
        print(f"基线引用 {commit or '未知'} 不是版本标签，跳过最低版本 {minimum} 的比较")
        return
    if got < need:
        raise SystemExit(f"当前基线 {commit} 低于插件要求的 {minimum}")


def ensure_requires(manifest: dict) -> None:
    requires = manifest.get("requires") or []
    if not isinstance(requires, list):
        raise SystemExit("plugin.yml 的 requires 必须是列表")
    for dep in requires:
        if not (ROOT / ".baseline/plugins" / f"{dep}.yml").is_file():
            raise SystemExit(f"插件 {manifest['name']} 依赖 {dep}，请先安装它")


def apply_inserts(manifest: dict, values: dict[str, str]) -> None:
    name = str(manifest["name"])
    inserts = manifest.get("inserts") or []
    if not isinstance(inserts, list):
        raise SystemExit("plugin.yml 的 inserts 必须是列表")
    for item in inserts:
        if not isinstance(item, dict):
            raise SystemExit("inserts 中有无法识别的条目")
        path = ROOT / str(item["file"])
        marker = str(item["marker"])
        token = f"plugin:{name}:{item['id']}"
        content = render(str(item.get("content") or ""), values)
        if token not in content:
            raise SystemExit(f"插入内容必须包含幂等标记 {token}")
        if not content.endswith("\n"):
            content += "\n"
        if not path.is_file():
            raise SystemExit(f"找不到 {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        if token in text:
            continue
        if marker not in text:
            raise SystemExit(f"{path.relative_to(ROOT)} 中找不到标记 {marker}")
        index = text.index(marker)
        line_start = text.rfind("\n", 0, index) + 1
        path.write_text(text[:line_start] + content + text[line_start:], encoding="utf-8")
        print(f"已插入 {path.relative_to(ROOT)}（{token}）")


def used_migration_versions() -> set[str]:
    found = set()
    root = ROOT / "db/migration"
    if not root.is_dir():
        return found
    for path in root.glob("*/*.sql"):
        match = VERSION_LINE.match(path.name)
        if match:
            found.add(match.group(1))
    return found


def allocate_versions(count: int) -> list[str]:
    used = used_migration_versions()
    current = int(datetime.now().strftime("%Y%m%d%H%M"))
    versions: list[str] = []
    while len(versions) < count:
        text = f"{current:012d}"
        if text not in used:
            versions.append(text)
            used.add(text)
        current += 1
    return versions


def write_data_file(values: dict[str, str]) -> Path:
    handle, name = tempfile.mkstemp(prefix="ane-plugin-data-", suffix=".yml")
    path = Path(name)
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    import os

    os.close(handle)
    return path


def run_copier(args: list[str]) -> None:
    command = [*copier_command(), *args]
    print("执行：" + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"copier 失败，退出码 {result.returncode}")


def answers_path(name: str) -> Path:
    return ROOT / ".baseline/plugins" / f"{name}.yml"


def ensure_recorded(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    if re.search(rf"^{re.escape(key)}:", text, re.M):
        return
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + f"{key}: {json.dumps(value, ensure_ascii=False)}\n", encoding="utf-8")


def copy_plugin(source: str, ref: str | None, values: dict[str, str]) -> dict[str, str]:
    versions = allocate_versions(2)
    data = dict(values)
    data["migration_version"] = versions[0]
    data["migration_version_2"] = versions[1]
    data_file = write_data_file(data)
    try:
        args = ["copy", "--trust", "--defaults", "--data-file", str(data_file)]
        if ref:
            args += ["--vcs-ref", ref]
        args += [source, str(ROOT)]
        run_copier(args)
    finally:
        data_file.unlink(missing_ok=True)
    return data


def check_manifest_name(manifest: dict, name: str) -> None:
    if str(manifest.get("name")) != name:
        raise SystemExit(f"清单名称是 {manifest.get('name')}，与参数 {name} 不一致")


def add(name: str, source: str | None, ref: str | None) -> int:
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", name):
        raise SystemExit("插件名只能包含小写字母、数字和连字符，并以字母开头")
    resolved = resolve_source(name, source)
    manifest = read_manifest(resolved, ref)
    check_manifest_name(manifest, name)
    values = project_values()
    recorded = answers_path(name)
    if recorded.is_file():
        apply_inserts(manifest, values)
        print(f"插件 {name} 已安装，已核对插入点")
        return 0
    ensure_baseline(manifest)
    ensure_requires(manifest)
    passed = copy_plugin(resolved, ref, values)
    if not recorded.is_file():
        raise SystemExit(f"插件模板没有写下 {recorded.relative_to(ROOT)}，请检查模板的 _answers_file")
    ensure_recorded(recorded, "migration_version", passed["migration_version"])
    ensure_recorded(recorded, "migration_version_2", passed["migration_version_2"])
    apply_inserts(manifest, values)
    print(f"已安装插件 {name}，迁移版本 {passed['migration_version']}")
    return 0


def update(name: str, version: str) -> int:
    recorded = answers_path(name)
    if not recorded.is_file():
        raise SystemExit(f"插件 {name} 尚未安装")
    source = read_src_path(recorded.read_text(encoding="utf-8"))
    if not source:
        raise SystemExit(f"{recorded.relative_to(ROOT)} 缺少 _src_path，无法升级")
    manifest = read_manifest(source, version)
    check_manifest_name(manifest, name)
    ensure_requires(manifest)
    run_copier(
        [
            "update",
            "--trust",
            "--defaults",
            "--answers-file",
            recorded.relative_to(ROOT).as_posix(),
            "--vcs-ref",
            version,
        ]
    )
    apply_inserts(manifest, project_values())
    print(f"已将插件 {name} 升级到 {version}")
    return 0


def add_selected() -> int:
    selected = read_plugins(answers_text())
    if not selected:
        print("未选择插件")
        return 0
    for name in selected:
        add(name, None, None)
    return 0


def list_plugins() -> int:
    catalog = load_catalog()
    directory = ROOT / ".baseline/plugins"
    installed = sorted(path.stem for path in directory.glob("*.yml")) if directory.is_dir() else []
    print("已安装：")
    if installed:
        for name in installed:
            print(f"  {name}")
    else:
        print("  （无）")
    print("目录：")
    if not catalog:
        print("  （空）")
        return 0
    for name in sorted(catalog):
        entry = catalog[name] if isinstance(catalog[name], dict) else {}
        state = "已安装" if name in installed else "未安装"
        description = entry.get("description") or ""
        print(f"  {name}  {state}  {description}")
    return 0


def self_check() -> int:
    catalog = parse_yaml('example:\n  description: 示例\n  local: plugins/example\n  git: ""\n')
    if catalog["example"]["local"] != "plugins/example" or catalog["example"]["git"] != "":
        raise SystemExit("目录解析结果不对")
    manifest = parse_yaml(
        'name: example\ninserts:\n  - file: backend/pom.xml\n    id: module\n    content: "a\\nb\\n"\n'
    )
    if manifest["inserts"][0]["content"] != "a\nb\n":
        raise SystemExit("字面量换行解析结果不对")
    if read_plugins("plugins: []\n") != []:
        raise SystemExit("空插件列表解析结果不对")
    if read_plugins("plugins:\n- example\n") != ["example"]:
        raise SystemExit("插件列表解析结果不对")
    if read_plugins('plugins:\n  - "example"\n_commit: abc\n') != ["example"]:
        raise SystemExit("缩进插件列表解析结果不对")
    rendered = render("{{ package_name }}-${project.version}", {"package_name": "com.dsmeta.park"})
    if rendered != "com.dsmeta.park-${project.version}":
        raise SystemExit("变量替换结果不对")
    print("插件清单解析通过")
    return 0


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="安装、查看和升级源码注入的插件")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="列出目录和已安装插件")
    sub.add_parser("add-selected", help="安装创建项目时勾选的插件")
    sub.add_parser("self-check", help="检查清单解析")
    add_parser = sub.add_parser("add", help="安装一个插件")
    add_parser.add_argument("name")
    add_parser.add_argument("--source", help="模板目录或 Git 地址，默认按插件目录解析")
    add_parser.add_argument("--ref", help="模板的标签或提交")
    update_parser = sub.add_parser("update", help="把已安装插件升级到指定标签")
    update_parser.add_argument("name")
    update_parser.add_argument("version")
    args = parser.parse_args(argv)
    if args.command == "list":
        return list_plugins()
    if args.command == "add-selected":
        return add_selected()
    if args.command == "self-check":
        return self_check()
    if args.command == "add":
        return add(args.name, args.source, args.ref)
    if args.command == "update":
        return update(args.name, args.version)
    parser.error(f"未知命令 {args.command}")
    return 2


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
