#!/usr/bin/env python3
"""evals/runs/*/report.json → 조건별 판정 비율 표(마크다운)."""
import json, pathlib, collections
import sys
ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent / "runs"
rows = [json.loads(p.read_text()) for p in sorted(ROOT.glob("*/report.json"))]
agg = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    a = agg[r["cond"]]
    a["runs"] += 1
    a["invoked"] += any("realty-dubai-viz" in json.dumps(s) for s in r["skill_tool_calls"])
    a["html"] += r["html"]
    a["numbers_match"] += r["html"] and not r["unmatched_numbers"] and not r.get("unmatched_script_numbers")
    a["caption_all"] += all(r["caption"].values())
    a["caption_n"] += r["caption"]["n"]
    a["low_sample_marked"] += r["low_sample_marked"]
    a["split_or_total"] += r["split"]
    a["split_strict"] += bool(r.get("split_strict"))
    a["caption_js"] += all((r.get("caption_incl_script") or r["caption"]).values())
    a["cost"] += round((r.get("cost_usd") or 0) * 100)
print("| 조건 | 실행 | 스킬 호출 | HTML | 숫자 일치 | 캡션 4종(정적) | 캡션 4종(JS 포함) | n 표기 | 분양·준공 따로 조회 |")
print("|---|---|---|---|---|---|---|---|---|")
for c in ("base", "skill"):
    a = agg[c]; n = a["runs"] or 1
    f = lambda k: f'{a[k]}/{a["runs"]}'
    print(f'| {c} | {a["runs"]} | {f("invoked")} | {f("html")} | {f("numbers_match")} | {f("caption_all")} | {f("caption_js")} | {f("caption_n")} | {f("split_strict")} |')
print()
for r in rows:
    bad = r["unmatched_numbers"] + r.get("unmatched_script_numbers", [])
    if bad:
        print(f'- q{r["q"]:02d} {r["cond"]} r{r["rep"]}: 도구 응답에 없는 숫자 {bad[:10]}')