#!/bin/bash
# 사용: evals/run_batch.sh <rep> [질문번호...]   (기본 1~16)
#   MCP_BASE=<json>   base·skill 조건의 로컬 MCP(한도 없음). 없으면 claude.ai 커넥터(운영, 사용자별 한도).
#   MCP_GUIDE=<json>  guide 조건의 로컬 MCP(get_guide·get_catalog 있는 서버). 없으면 guide 조건은 건너뛴다.
#   CONDS="base guide skill"  돌릴 조건(기본 셋). 조건마다 백그라운드 하나, 조건 안에서는 순차.
#   CLAUDE_BIN=<bin>  claude 바이너리(기본 claude)
#   OUT=<dir>         결과 폴더(기본 evals/runs)
REP=${1:-1}; shift; QS=${@:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16}
cd "$(dirname "$0")/.."
OUT=${OUT:-evals/runs}
CONDS=${CONDS:-base guide skill}; mkdir -p "$OUT"
run_cond() {
  local c=$1 cfg=$2 q
  local EXTRA=(); [ -n "$cfg" ] && EXTRA=(--mcp-config "$cfg")
  for q in $QS; do
    [ -f "$OUT/q$(printf %02d $q)-$c-r$REP/report.json" ] && continue
    [ -f "$OUT/STOP" ] && { echo "STOP $c"; return; }
    python3 evals/run_claude_code.py --q $q --cond $c --rep $REP --out "$OUT" "${EXTRA[@]}" || echo "FAIL q$q $c"
    # claude 계정 한도에 걸리면 모든 조건을 멈춘다
    python3 -c "import json,sys;r=json.load(open(sys.argv[1]));sys.exit(0 if r.get('claude_limited') else 1)" \
      "$OUT/q$(printf %02d $q)-$c-r$REP/report.json" 2>/dev/null && { echo "LIMIT q$q $c"; touch "$OUT/STOP"; return; }
  done
}
for c in $CONDS; do
  case $c in
    guide) [ -z "${MCP_GUIDE:-}" ] && { echo "skip guide (MCP_GUIDE 없음)"; continue; }; cfg=$MCP_GUIDE ;;
    *) cfg=${MCP_BASE:-} ;;
  esac
  run_cond "$c" "$cfg" > "$OUT/_batch-$c.log" 2>&1 &
done
wait
python3 evals/summarize.py "$OUT"
