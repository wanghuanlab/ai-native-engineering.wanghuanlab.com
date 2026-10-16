#!/usr/bin/env bash
# 升级路径测试：对 docs/releases/deployments.md「在用版本」中的每个版本，
# 先执行该版本的全部迁移脚本，再执行当前分支新增的脚本，确认客户现场可以平滑升级。
# 只验证 PostgreSQL 方言；信创方言在客户测试环境验证，结果写入部署回执。
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib/pg.sh

DIR="db/migration/postgresql"
VERSIONS=$(awk '/^## 在用版本/{f=1;next} /^## /{f=0} f' docs/releases/deployments.md |
  grep -oE '^- v[0-9]+\.[0-9]+\.[0-9]+' | cut -c3- | sort -u || true)

if [ -z "${VERSIONS}" ]; then
  echo "deployments.md 中没有在用版本，跳过升级路径测试"
  exit 0
fi

trap pg_stop EXIT
pg_start
CURRENT=$(ls "${DIR}"/V*.sql 2>/dev/null | xargs -n1 basename | sort)

for v in ${VERSIONS}; do
  if ! git rev-parse --verify --quiet "${v}^{commit}" >/dev/null; then
    echo "✗ 找不到版本标签 ${v}，发布时必须打标签" >&2
    exit 1
  fi
  echo "· 从 ${v} 升级"
  pg_reset
  OLD=$(git ls-tree --name-only "${v}" "${DIR}/" | xargs -n1 basename 2>/dev/null | grep '^V.*\.sql$' | sort || true)
  for f in ${OLD}; do
    git show "${v}:${DIR}/${f}" | pg_exec
  done
  for f in $(comm -13 <(echo "${OLD}") <(echo "${CURRENT}")); do
    echo "  执行 ${f}"
    pg_exec <"${DIR}/${f}"
  done
done
echo "升级路径测试通过：${VERSIONS//$'\n'/, }"
