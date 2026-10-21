#!/usr/bin/env bash
# 统一校验入口。
#   quick     AI 配置 + 迁移脚本 + 后端单元测试 + 前端检查（提交前、推送前）
#   full      quick + 集成测试 + 前端构建 + 测试删除检查 + 密钥扫描 + 升级路径（TL 合并前）
#   ai | db | backend | frontend | upgrade   单项校验
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-quick}"
RESULTS=()

step() {
  local name="$1"
  shift
  local status
  echo "▶ ${name}"
  # if/&&/|| 会让其中的函数忽略 set -e，多条命令时前面的失败会被最后一条成功命令掩盖。
  # 在独立子 shell 里重新打开 set -e，任一命令失败都会让整个步骤失败。
  set +e
  (
    set -e
    "$@"
  )
  status=$?
  set -e
  if [ "${status}" -eq 0 ]; then
    RESULTS+=("✓ ${name}")
  else
    RESULTS+=("✗ ${name}")
    summary
    exit 1
  fi
}

summary() {
  echo
  echo "──────── 校验结果（${MODE}）"
  printf '%s\n' "${RESULTS[@]}"
}

run_ai() { python3 scripts/build-ai-config.py --check; }
run_db() { python3 scripts/lib/checks.py migrations; }

run_backend() {
  local goal="$1"
  (cd backend && ./mvnw -B -q spotless:check "${goal}")
}

run_frontend() {
  local with_build="$1"
  # 逐条检查退出码：即使调用方把本函数放进条件表达式，也不能靠 set -e 中止。
  (
    cd frontend || exit
    if [ ! -d node_modules ]; then
      if [ -f pnpm-lock.yaml ]; then
        CI=true pnpm install --frozen-lockfile || exit
      else
        CI=true pnpm install || exit
      fi
    fi
    pnpm -s gen:api || exit
    pnpm -s typecheck || exit
    pnpm -s lint || exit
    pnpm -s format:check || exit
    pnpm -s test || exit
    if [ "${with_build}" = "build" ]; then
      pnpm -s build || exit
    fi
  )
}

run_test_guard() { python3 scripts/lib/checks.py test-guard; }
run_secrets() { python3 scripts/lib/checks.py secrets --all; }
run_upgrade() { scripts/upgrade-path.sh; }

case "${MODE}" in
  ai) step "AI 配置一致性" run_ai ;;
  db) step "迁移脚本" run_db ;;
  backend) step "后端格式与单元测试" run_backend test ;;
  frontend) step "前端检查" run_frontend nobuild ;;
  upgrade) step "升级路径" run_upgrade ;;
  quick)
    step "AI 配置一致性" run_ai
    step "迁移脚本" run_db
    step "后端格式与单元测试" run_backend test
    step "前端检查" run_frontend nobuild
    ;;
  full)
    step "AI 配置一致性" run_ai
    step "迁移脚本" run_db
    step "测试删除检查" run_test_guard
    step "密钥扫描" run_secrets
    step "后端格式、单元测试与集成测试" run_backend verify
    step "前端检查与构建" run_frontend build
    step "升级路径" run_upgrade
    ;;
  *)
    echo "用法：$0 [quick|full|ai|db|backend|frontend|upgrade]" >&2
    exit 2
    ;;
esac

summary
