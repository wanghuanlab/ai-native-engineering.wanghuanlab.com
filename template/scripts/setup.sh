#!/usr/bin/env bash
# 新成员克隆项目后执行一次：检查工具、启用 Git 钩子、生成 AI 配置、安装前端依赖。
set -euo pipefail
cd "$(dirname "$0")/.."

missing=0
check() {
  local name="$1" cmd="$2" hint="$3"
  if command -v "${cmd}" >/dev/null 2>&1; then
    echo "✓ ${name}"
  else
    echo "✗ ${name}：${hint}"
    missing=1
  fi
}
check "Java 21" java "安装 JDK 21（如 Temurin 21）"
check "Docker" docker "集成测试、表结构摘要和升级路径测试需要 Docker"
check "Node.js" node "安装 Node.js 22 或更高版本"
check "pnpm" pnpm "执行 corepack enable 或 npm i -g pnpm@11"
check "Python 3" python3 "安装 Python 3.10 或更高版本"

if command -v java >/dev/null 2>&1; then
  java_major=$(java -XshowSettings:properties -version 2>&1 | awk -F'= ' '/java.specification.version/{print $2}')
  [ "${java_major}" -ge 21 ] 2>/dev/null || { echo "✗ 当前 Java 版本为 ${java_major}，需要 21 或更高"; missing=1; }
fi
[ "${missing}" = 0 ] || { echo "请先安装缺失的工具"; exit 1; }

git config core.hooksPath .githooks
chmod +x .githooks/* scripts/*.sh backend/mvnw
echo "✓ 已启用 Git 钩子（.githooks/）"

python3 scripts/build-ai-config.py
(cd frontend && CI=true pnpm install)

if [ -z "$(git config user.name || true)" ]; then
  echo "! 请设置 git user.name，需与 .baseline/project.json 中 techLeads 的写法一致（若你是技术负责人）"
fi
echo
echo "完成。下一步：./scripts/verify.sh quick；协作流程见 docs/context/collaboration.md"
