#!/bin/bash
# 本地预览：blob 抓取要求 http 环境，不能直接 file:// 打开。
# 用法：bash scripts/serve.sh [端口，默认 8765]
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8766}"
cd "$ROOT/site"
echo "serving $ROOT/site at http://localhost:$PORT"
exec /usr/bin/python3 -m http.server "$PORT"
