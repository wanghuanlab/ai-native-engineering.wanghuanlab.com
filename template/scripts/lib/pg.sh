# 临时 PostgreSQL 容器工具函数，供 db-schema.sh 和 upgrade-path.sh 使用。
# shellcheck shell=bash

PG_IMAGE="${PG_IMAGE:-postgres:17-alpine}"
PG_CONTAINER=""

pg_start() {
  command -v docker >/dev/null || { echo "需要 Docker" >&2; return 1; }
  PG_CONTAINER="baseline-pg-$$-${RANDOM}"
  docker run -d --rm --name "${PG_CONTAINER}" -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=app "${PG_IMAGE}" >/dev/null
  local ok=0
  for _ in $(seq 1 60); do
    if docker exec "${PG_CONTAINER}" psql -U postgres -d app -qtAc 'select 1' >/dev/null 2>&1; then
      ok=$((ok + 1))
      [ "${ok}" -ge 2 ] && return 0
    fi
    sleep 1
  done
  echo "PostgreSQL 容器启动超时" >&2
  return 1
}

pg_stop() {
  [ -n "${PG_CONTAINER}" ] && docker rm -f "${PG_CONTAINER}" >/dev/null 2>&1 || true
}

pg_reset() {
  docker exec "${PG_CONTAINER}" psql -U postgres -d app -qc 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' >/dev/null
}

# 从标准输入执行 SQL
pg_exec() {
  docker exec -i "${PG_CONTAINER}" psql -U postgres -d app -q -v ON_ERROR_STOP=1 >/dev/null
}

pg_query() {
  docker exec "${PG_CONTAINER}" psql -U postgres -d app -qtA -F $'\t' -c "$1"
}
