# Git 钩子共用的 Python 查找。
# Git for Windows 用自带的 sh 执行钩子，所以这里只用 POSIX sh，不依赖 bash 4 或 macOS 工具。
# 业务检查都在 Python 里。
py() {
  if command -v python3 >/dev/null 2>&1; then
    python3 "$@"
  elif command -v python >/dev/null 2>&1; then
    python "$@"
  elif command -v py >/dev/null 2>&1; then
    py -3 "$@"
  else
    echo "需要 Python 3.10 或更高版本（python3、python 或 py -3）" >&2
    return 127
  fi
}
