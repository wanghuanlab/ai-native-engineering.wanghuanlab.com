#!/usr/bin/env python3
"""创建后端业务模块：Maven 子模块、分层包结构、空契约，并登记到父 POM、app 和架构文档。

  new-module.sh <模块名> [--title 中文名]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = re.compile(r"^[a-z][a-z0-9]{1,19}$")
LAYERS = {
    "api": "{title}模块对其他模块开放的接口。其他模块只能依赖这个包，不能依赖本模块的其他包。",
    "web": "{title}模块的接口层：控制器实现契约生成的接口，只做参数转换，不写业务逻辑、不开事务。",
    "service": "{title}模块的应用服务：事务边界、业务编排、调用领域对象。",
    "domain": "{title}模块的领域层：实体、值对象、仓储接口、错误码。不依赖 web、service、infra。",
    "infra": "{title}模块的基础设施：外部系统适配、复杂查询实现。",
}

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>{group}</groupId>
        <artifactId>{code}-parent</artifactId>
        <version>0.1.0-SNAPSHOT</version>
        <relativePath>../../pom.xml</relativePath>
    </parent>

    <artifactId>{code}-module-{name}</artifactId>
    <name>{project} - {title}模块</name>

    <dependencies>
        <dependency>
            <groupId>{group}</groupId>
            <artifactId>{code}-common</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.openapitools</groupId>
                <artifactId>openapi-generator-maven-plugin</artifactId>
                <executions>
                    <execution>
                        <id>contract</id>
                        <goals>
                            <goal>generate</goal>
                        </goals>
                        <configuration>
                            <inputSpec>${{contracts.dir}}/{name}.yaml</inputSpec>
                            <apiPackage>{package}.{name}.web.api</apiPackage>
                            <modelPackage>{package}.{name}.web.dto</modelPackage>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
"""

CONTRACT = """openapi: 3.0.3
info:
  title: {title}模块
  version: 1.0.0
servers:
  - url: /
# 接口路径统一为 /api/{name}/...，公共结构引用 ./common.yaml。写法参考 docs/context/architecture.md
paths: {{}}
"""


def insert_before(path: Path, marker: str, snippet: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        raise SystemExit(f"{path.relative_to(ROOT)} 中找不到标记 {marker}，请手工登记")
    index = text.index(marker)
    line_start = text.rfind("\n", 0, index) + 1
    path.write_text(text[:line_start] + snippet + text[line_start:], encoding="utf-8")


def next_error_segment(architecture: Path) -> str:
    used = {int(m) for m in re.findall(r"\|\s*B(\d{2})xx\s*\|", architecture.read_text(encoding="utf-8"))}
    for n in range(10, 99):
        if n not in used:
            return f"B{n:02d}xx"
    raise SystemExit("错误码号段已用完")


def main() -> int:
    parser = argparse.ArgumentParser(description="创建后端业务模块")
    parser.add_argument("name", help="模块名，小写字母开头，只含小写字母和数字，如 visitor")
    parser.add_argument("--title", help="模块中文名，默认与模块名相同")
    args = parser.parse_args()
    name, title = args.name, args.title or args.name
    if not NAME.match(name):
        print("模块名只能包含小写字母和数字，以字母开头，2～20 个字符", file=sys.stderr)
        return 2

    project = json.loads((ROOT / ".baseline/project.json").read_text(encoding="utf-8"))
    package = project["packageName"]
    values = {
        "group": package,
        "code": project["projectCode"],
        "project": project["projectName"],
        "package": package,
        "name": name,
        "title": title,
    }
    module_dir = ROOT / "backend/modules" / name
    contract = ROOT / "contracts/openapi" / f"{name}.yaml"
    if module_dir.exists() or contract.exists():
        print(f"模块 {name} 已存在", file=sys.stderr)
        return 1

    module_dir.mkdir(parents=True)
    (module_dir / "pom.xml").write_text(POM.format(**values), encoding="utf-8")
    java_root = module_dir / "src/main/java" / package.replace(".", "/") / name
    for layer, doc in LAYERS.items():
        directory = java_root / layer
        directory.mkdir(parents=True)
        lines = [f"/** {doc.format(title=title)} */"]
        if layer == "api":
            lines += ['@NamedInterface("api")', f"package {package}.{name}.{layer};", "", "import org.springframework.modulith.NamedInterface;"]
        else:
            lines += [f"package {package}.{name}.{layer};"]
        (directory / "package-info.java").write_text("\n".join(lines) + "\n", encoding="utf-8")
    test_dir = module_dir / "src/test/java" / package.replace(".", "/") / name / "domain"
    test_dir.mkdir(parents=True)
    (test_dir / ".gitkeep").touch()
    contract.write_text(CONTRACT.format(**values), encoding="utf-8")

    insert_before(ROOT / "backend/pom.xml", "<!-- @modules-end -->", f"        <module>modules/{name}</module>\n")
    insert_before(
        ROOT / "backend/app/pom.xml",
        "<!-- @module-deps-end -->",
        f"        <dependency>\n            <groupId>{package}</groupId>\n"
        f"            <artifactId>{values['code']}-module-{name}</artifactId>\n"
        f"            <version>${{project.version}}</version>\n        </dependency>\n",
    )

    architecture = ROOT / "docs/context/architecture.md"
    segment = next_error_segment(architecture)
    insert_before(architecture, "<!-- @module-table-end -->", f"| `{name}` | {title} | {segment} | 待补充职责 |\n")

    print(f"已创建模块 {name}（错误码号段 {segment}）：")
    print(f"  backend/modules/{name}/、contracts/openapi/{name}.yaml")
    print("  已登记到 backend/pom.xml、backend/app/pom.xml、docs/context/architecture.md")
    print("下一步：在契约中定义接口，补充 architecture.md 中的模块职责，然后执行 ./scripts/verify.sh backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
