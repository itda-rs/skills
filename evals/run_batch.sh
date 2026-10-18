#!/bin/bash
# 사용: evals/run_batch.sh <rep> [질문번호...]   (기본 1~10). MCP 한도(5시간 150회) 때문에 한 배치 = 1회차.
REP=${1:-1}; shift; QS=${@:-1 2 3 4 5 6 7 8 9 10}
cd "$(dirname "$0")/.."
for q in $QS; do for c in base skill; do
  [ -f evals/runs/q$(printf %02d $q)-$c-r$REP/report.json ] && continue
  python3 evals/run_claude_code.py --q $q --cond $c --rep $REP || echo "FAIL q$q $c"
done; done
python3 evals/summarize.py
