#!/usr/bin/env bash
# 生成交付包：./scripts/release-pack.sh v1.3.0 [--images]
# 前提：版本标签已存在且指向当前提交；docs/releases/<版本>/ 下已有 release-notes.md、deploy-guide.md、upgrade-guide.md。
# 由 TL 执行。--images 时用 docker buildx 构建 amd64 与 arm64 镜像并导出为离线包。
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:?用法：$0 <版本，如 v1.3.0> [--images]}"
WITH_IMAGES="${2:-}"
CODE=$(python3 -c 'import json; print(json.load(open(".baseline/project.json"))["projectCode"])')
DIALECTS=$(python3 -c 'import json; print(" ".join(json.load(open(".baseline/project.json"))["dialects"]))')
DOCS="docs/releases/${VERSION}"
OUT="dist/${CODE}-${VERSION}"

[[ "${VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "版本格式应为 vMAJOR.MINOR.PATCH" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "工作区有未提交的改动" >&2; exit 1; }
[ "$(git rev-parse "${VERSION}^{commit}" 2>/dev/null)" = "$(git rev-parse HEAD)" ] ||
  { echo "请先在当前提交上打标签：git tag -a ${VERSION} -m ${VERSION}" >&2; exit 1; }
for f in release-notes.md deploy-guide.md upgrade-guide.md; do
  [ -f "${DOCS}/${f}" ] || { echo "缺少 ${DOCS}/${f}（模板见 docs/_templates/）" >&2; exit 1; }
done

rm -rf "${OUT}" && mkdir -p "${OUT}"/{app,db,config}
(cd backend && ./mvnw -B -q package -DskipTests)
(cd frontend && pnpm -s gen:api && pnpm -s build)

cp "backend/app/target/${CODE}-app.jar" "${OUT}/app/"
cp -R frontend/apps/admin/dist "${OUT}/app/admin"
[ -d frontend/apps/screen/dist ] && cp -R frontend/apps/screen/dist "${OUT}/app/screen"
for d in ${DIALECTS}; do
  mkdir -p "${OUT}/db/${d}" && cp db/migration/"${d}"/V*.sql "${OUT}/db/${d}/" 2>/dev/null || true
done
cp backend/app/src/main/resources/application*.yml "${OUT}/config/"
cp "${DOCS}"/*.md "${OUT}/"

if [ "${WITH_IMAGES}" = "--images" ]; then
  mkdir -p "${OUT}/images"
  for arch in amd64 arm64; do
    for svc in backend frontend; do
      docker buildx build --platform "linux/${arch}" -f "deploy/docker/${svc}.Dockerfile" \
        -t "${CODE}-${svc}:${VERSION}" --output "type=docker,dest=${OUT}/images/${CODE}-${svc}-${VERSION}-${arch}.tar" .
    done
  done
fi

(cd "${OUT}" && find . -type f ! -name checksums.txt -print0 | sort -z | xargs -0 shasum -a 256 >checksums.txt)
tar -C dist -czf "dist/${CODE}-${VERSION}.tar.gz" "${CODE}-${VERSION}"
echo "交付包：dist/${CODE}-${VERSION}.tar.gz"
