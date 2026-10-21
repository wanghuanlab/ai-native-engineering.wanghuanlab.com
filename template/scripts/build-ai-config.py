#!/usr/bin/env python3
"""把 .ai/rules/、.ai/project/ 和 .ai/skills/ 编译为各 AI 工具的配置文件。

输出：
  AGENTS.md              通用入口（Codex 等工具读取），不超过 150 行
  CLAUDE.md              Claude Code 入口，引用 AGENTS.md
  .cursor/rules/*.mdc    Cursor 规则，按目录或文件类型自动挂载
  <工具>/skills/<名称>/   各工具的 Skills 目录（内容与 .ai/skills/ 相同）

用法：
  python3 scripts/build-ai-config.py           生成
  python3 scripts/build-ai-config.py --check   只检查生成结果是否与规则源一致（门禁使用）
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULE_DIRS = [ROOT / ".ai" / "rules", ROOT / ".ai" / "project"]
SKILLS_DIR = ROOT / ".ai" / "skills"
SKILL_TARGETS = [".cursor/skills", ".claude/skills", ".agents/skills"]
CURSOR_RULES_DIR = ".cursor/rules"
MAX_AGENTS_LINES = 150
GENERATED_NOTE = "由 scripts/build-ai-config.py 生成，禁止手改；请修改 .ai/rules/、.ai/project/ 或 .ai/skills/"
SECURITY_TEXT = {
    "normal": "普通：可使用部门批准的云端 AI 工具",
    "restricted": "受限：仅可使用国内合规云服务或私有化部署模型",
    "classified": "涉密：仅可使用私有化部署模型，禁止用云端 AI 工具打开本仓库",
}


@dataclass
class Rule:
    id: str
    title: str
    scope: str
    summary: str
    globs: list[str] = field(default_factory=list)
    body: str = ""
    path: str = ""


def parse_front_matter(text: str, source: Path) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise SystemExit(f"{source}: 缺少文件头（--- 开头的元数据）")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise SystemExit(f"{source}: 文件头没有结束标记 ---")
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise SystemExit(f"{source}: 文件头格式错误：{line}")
        meta[key.strip()] = value.strip()
    return meta, text[end + 5 :].lstrip("\n")


def load_rules() -> list[Rule]:
    rules: list[Rule] = []
    for directory in RULE_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
            for key in ("id", "title", "scope", "summary"):
                if key not in meta:
                    raise SystemExit(f"{path}: 文件头缺少 {key}")
            scope = meta["scope"]
            if scope not in ("always", "glob", "requested"):
                raise SystemExit(f"{path}: scope 只能是 always、glob 或 requested")
            globs = [g.strip() for g in meta.get("globs", "").split(",") if g.strip()]
            if scope == "glob" and not globs:
                raise SystemExit(f"{path}: scope 为 glob 时必须提供 globs")
            rules.append(
                Rule(
                    id=meta["id"],
                    title=meta["title"],
                    scope=scope,
                    summary=meta["summary"],
                    globs=globs,
                    body=body.rstrip() + "\n",
                    path=path.relative_to(ROOT).as_posix(),
                )
            )
    ids = [r.id for r in rules]
    duplicated = {i for i in ids if ids.count(i) > 1}
    if duplicated:
        raise SystemExit(f"规则 id 重复：{', '.join(sorted(duplicated))}")
    return sorted(rules, key=lambda r: r.id)


def load_skills() -> list[tuple[str, str, Path]]:
    skills = []
    if SKILLS_DIR.is_dir():
        for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            meta, _ = parse_front_matter(path.read_text(encoding="utf-8"), path)
            if meta.get("name") != path.parent.name:
                raise SystemExit(f"{path}: name 必须与目录名一致")
            skills.append((meta["name"], meta.get("description", ""), path.parent))
    return skills


def strip_comments(body: str) -> str:
    return "\n".join(line for line in body.splitlines() if not line.strip().startswith("<!--")).strip() + "\n"


def render_agents(project: dict, rules: list[Rule], skills: list[tuple[str, str, Path]]) -> str:
    profiles = [name for name, enabled in (("信创", project["profiles"]["xinchuang"]), ("大屏", project["profiles"]["screen"])) if enabled]
    lines = [
        f"<!-- {GENERATED_NOTE} -->",
        f"# {project['projectName']}（{project['projectCode']}）AI 协作说明",
        "",
        f"- 密级：{SECURITY_TEXT[project['securityLevel']]}",
        f"- 技术负责人：{', '.join(project['techLeads'])}",
        f"- 画像：{', '.join(profiles) if profiles else '标准业务系统'}；数据库方言：{', '.join(project['dialects'])}",
        "- 技术栈：Java 21 + Spring Boot + Spring Data JPA（`backend/`）；Vue 3 + TypeScript + Element Plus（`frontend/`）；"
        "OpenAPI 契约（`contracts/openapi/`）；迁移脚本（`db/migration/`）",
        "",
    ]
    for rule in (r for r in rules if r.scope == "always"):
        body_lines = strip_comments(rule.body).splitlines()
        if body_lines and body_lines[0].startswith("# "):
            body_lines = body_lines[1:]
        body = "\n".join("#" + line if line.startswith("## ") else line for line in body_lines)
        lines += [f"## {rule.title}", "", body.strip(), ""]
    lines += ["## 按需阅读的规则", "", "| 何时读 | 文件 |", "| :--- | :--- |"]
    for rule in (r for r in rules if r.scope != "always"):
        when = rule.summary + (f"（{', '.join(f'`{g}`' for g in rule.globs)}）" if rule.globs else "")
        lines.append(f"| {when} | `{rule.path}` |")
    lines += ["", "## Skills（标准工作流，位于 `.ai/skills/`）", "", "| Skill | 用途 |", "| :--- | :--- |"]
    for name, description, _ in skills:
        lines.append(f"| `{name}` | {description.split('。')[0]} |")
    lines += [
        "",
        "## 上下文入口",
        "",
        "- 术语 `docs/context/glossary.md`；模块与错误码号段 `docs/context/architecture.md`；表结构 `docs/context/db-schema.md`",
        "- 踩坑记录 `docs/context/pitfalls.md`；当前规格 `docs/specs/`；进行中的变更 `docs/changes/`",
        "- 产物模板 `docs/_templates/`；填写完整的示范变更包 `docs/_templates/examples/REQ-20261015-visitor-approval/`（写任何产物前先看对应的示范）",
        "",
        "## 常用命令",
        "",
        "- 快速校验：`./scripts/verify.sh quick`（Windows：`scripts\\verify.cmd quick`）；完整校验：`./scripts/verify.sh full`",
        "- 新建变更包：`./scripts/new-change.sh <短名> --level M|L`（Windows 把 `.sh` 换成 `.cmd`）；新建后端模块同理",
        "- 生成前端接口客户端：`cd frontend && pnpm gen:api`；更新表结构摘要：`./scripts/db-schema.sh`",
        "- 后端格式化：`cd backend && ./mvnw spotless:apply`（Windows：`mvnw.cmd`）；前端格式化：`cd frontend && pnpm format`",
        "",
    ]
    text = "\n".join(lines)
    count = text.count("\n")
    if count > MAX_AGENTS_LINES:
        raise SystemExit(f"AGENTS.md 有 {count} 行，超过 {MAX_AGENTS_LINES} 行上限。请精简 scope 为 always 的规则。")
    return text


def render_claude() -> str:
    return (
        f"<!-- {GENERATED_NOTE} -->\n"
        "@AGENTS.md\n\n"
        "## Claude Code 补充说明\n\n"
        "- Skills 位于 `.claude/skills/`，与 `.ai/skills/` 内容相同。\n"
        "- 按需阅读的规则请按 AGENTS.md 中的表格用 Read 工具读取对应文件。\n"
    )


def render_mdc(rule: Rule) -> str:
    header = ["---", f"description: {rule.title}：{rule.summary}"]
    header.append(f"globs: {','.join(rule.globs)}" if rule.scope == "glob" else "globs:")
    header.append(f"alwaysApply: {'true' if rule.scope == 'always' else 'false'}")
    header.append("---")
    return "\n".join(header) + f"\n<!-- {GENERATED_NOTE} -->\n\n" + strip_comments(rule.body)


def build_outputs() -> dict[str, bytes]:
    project = json.loads((ROOT / ".baseline" / "project.json").read_text(encoding="utf-8"))
    rules = load_rules()
    skills = load_skills()
    outputs: dict[str, bytes] = {
        "AGENTS.md": render_agents(project, rules, skills).encode(),
        "CLAUDE.md": render_claude().encode(),
    }
    for rule in rules:
        outputs[f"{CURSOR_RULES_DIR}/{rule.id}.mdc"] = render_mdc(rule).encode()
    for target in SKILL_TARGETS:
        for name, _, directory in skills:
            for file in sorted(p for p in directory.rglob("*") if p.is_file()):
                outputs[f"{target}/{name}/{file.relative_to(directory).as_posix()}"] = file.read_bytes()
    return outputs


def managed_existing() -> set[str]:
    existing = {p for p in ("AGENTS.md", "CLAUDE.md") if (ROOT / p).exists()}
    for directory in [CURSOR_RULES_DIR, *SKILL_TARGETS]:
        base = ROOT / directory
        if base.is_dir():
            existing |= {p.relative_to(ROOT).as_posix() for p in base.rglob("*") if p.is_file()}
    return existing


def main() -> int:
    outputs = build_outputs()
    existing = managed_existing()
    if "--check" in sys.argv:
        stale = sorted(existing - outputs.keys())
        changed = sorted(p for p, data in outputs.items() if not (ROOT / p).exists() or (ROOT / p).read_bytes() != data)
        if stale or changed:
            print("AI 配置与规则源不一致，请运行 python3 scripts/build-ai-config.py 并提交结果：", file=sys.stderr)
            for p in changed:
                print(f"  需要更新：{p}", file=sys.stderr)
            for p in stale:
                print(f"  需要删除：{p}", file=sys.stderr)
            return 1
        print("AI 配置与规则源一致")
        return 0
    for path in existing - outputs.keys():
        (ROOT / path).unlink()
    for directory in [CURSOR_RULES_DIR, *SKILL_TARGETS]:
        base = ROOT / directory
        if base.is_dir():
            for d in sorted((p for p in base.rglob("*") if p.is_dir()), reverse=True):
                if not any(d.iterdir()):
                    d.rmdir()
    for path, data in outputs.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
    print(f"已生成 AGENTS.md、CLAUDE.md、{CURSOR_RULES_DIR}/ 和 {len(SKILL_TARGETS)} 个工具的 Skills 目录")
    return 0


if __name__ == "__main__":
    sys.exit(main())
