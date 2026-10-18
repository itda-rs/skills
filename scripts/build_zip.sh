#!/bin/bash
# claude.ai 업로드용 스킬 zip 만들기: dist/realty-dubai-viz-<version>.zip
# 사용: scripts/build_zip.sh   (버전은 plugin.json 에서 읽는다)
set -euo pipefail
cd "$(dirname "$0")/.."
VER=$(python3 -c 'import json;print(json.load(open("plugins/realty-dubai/.claude-plugin/plugin.json"))["version"])')
mkdir -p dist
OUT="dist/realty-dubai-viz-$VER.zip"
rm -f "$OUT"
(cd plugins/realty-dubai/skills && zip -qr -X "../../../$OUT" realty-dubai-viz -x '*.DS_Store')
unzip -l "$OUT"
echo "$OUT"
