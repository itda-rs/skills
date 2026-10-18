#!/bin/bash
# 사용: evals/run_batch.sh <rep> [질문번호...]   (기본 1~10)
#   MCP_CONFIG=<json>  로컬 MCP(한도 없음)로 돌린다. 없으면 claude.ai 커넥터(운영, 사용자별 한도).
#   OUT=<dir>          결과 폴더(기본 evals/runs)
REP=${1:-1}; shift; QS=${@:-1 2 3 4 5 6 7 8 9 10}
cd "$(dirname "$0")/.."
OUT=${OUT:-evals/runs}
EXTRA=(); [ -n "${MCP_CONFIG:-}" ] && EXTRA=(--mcp-config "$MCP_CONFIG")
for q in $QS; do for c in base skill; do
  [ -f "$OUT/q$(printf %02d $q)-$c-r$REP/report.json" ] && continue
  python3 evals/run_claude_code.py --q $q --cond $c --rep $REP --out "$OUT" "${EXTRA[@]}" || echo "FAIL q$q $c"
done; done
python3 evals/summarize.py "$OUT"
