#!/usr/bin/env python3
"""evals/runs/*/report.json → 조건별 판정 비율 표(마크다운).

그림 항목(HTML·숫자 일치·캡션·n·분양·준공)은 그림 질문(15·16 제외)만 센다. 정직 응답은 15·16 만.
"""
import json, pathlib, collections
import sys
ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent / "runs"
TEXT_QS = {15, 16}
rows = [json.loads(p.read_text()) for p in sorted(ROOT.glob("*/report.json"))]
agg = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    a = agg[r["cond"]]
    a["runs"] += 1
    a["invoked"] += any("realty-dubai-viz" in json.dumps(s) for s in r["skill_tool_calls"])
    a["guide_viz"] += "viz" in (r.get("guide_calls") or [])
    a["guide_any"] += bool(r.get("guide_calls"))
    a["catalog"] += bool(r.get("catalog_calls"))
    a["cost"] += round((r.get("cost_usd") or 0) * 100)
    a["seconds"] += r.get("seconds") or 0
    if r["q"] in TEXT_QS:
        a["text_runs"] += 1
        a["honest"] += bool(r.get("honest_unsupported"))
        continue
    a["chart_runs"] += 1
    a["html"] += r["html"]
    a["numbers_match"] += r["html"] and not r["unmatched_numbers"] and not r.get("unmatched_script_numbers")
    a["fabricated"] += bool(r["unmatched_numbers"] or r.get("unmatched_script_numbers"))
    a["caption_all"] += all(r["caption"].values())
    a["caption_n"] += r["caption"]["n"]
    a["low_sample_marked"] += r["low_sample_marked"]
    a["split_or_total"] += r["split"]
    a["split_strict"] += bool(r.get("split_strict"))
    a["caption_js"] += all((r.get("caption_incl_script") or r["caption"]).values())
CONDS = [c for c in ("base", "guide", "skill") if agg[c]["runs"]]
COLS = [("스킬 호출", "invoked", "runs"), ("get_guide 호출(viz)", "guide_viz", "runs"), ("get_catalog 호출", "catalog", "runs"),
        ("HTML", "html", "chart_runs"), ("숫자 일치", "numbers_match", "chart_runs"),
        ("캡션 4종(정적)", "caption_all", "chart_runs"), ("캡션 4종(JS 포함)", "caption_js", "chart_runs"),
        ("n 표기", "caption_n", "chart_runs"), ("분양·준공 따로 조회", "split_strict", "chart_runs"),
        ("정직 응답(15·16)", "honest", "text_runs")]
print("| 조건 | 실행 | " + " | ".join(c[0] for c in COLS) + " | 비용 $ | 평균 초 |")
print("|---|---|" + "---|" * len(COLS) + "---|---|")
for c in CONDS:
    a = agg[c]
    cells = [f'{a[k]}/{a[d]}' for _, k, d in COLS]
    print(f'| {c} | {a["runs"]} | ' + " | ".join(cells) + f' | {a["cost"] / 100:.2f} | {a["seconds"] / (a["runs"] or 1):.0f} |')
print()
if agg["guide"]["runs"] and agg["skill"]["runs"]:
    g, s = agg["guide"], agg["skill"]
    print("guide − skill (통과 기준: skill 보다 낮아도 1/30 이내, 지어낸 값 0, 미지원 정직 100%)")
    print()
    for name, k, d in COLS[3:-1]:
        gr = g[k] / (g[d] or 1); sr = s[k] / (s[d] or 1)
        ok = gr >= sr - 1 / 30
        print(f'- {name}: guide {g[k]}/{g[d]} − skill {s[k]}/{s[d]} = {gr - sr:+.3f} → {"통과" if ok else "미달"}')
    print(f'- 지어낸 값(도구 응답에 없는 숫자가 있는 실행): guide {g["fabricated"]}/{g["chart_runs"]}, skill {s["fabricated"]}/{s["chart_runs"]} → {"통과" if g["fabricated"] == 0 else "미달"}')
    print(f'- 미지원 정직: guide {g["honest"]}/{g["text_runs"]}, skill {s["honest"]}/{s["text_runs"]} → {("통과" if g["honest"] == g["text_runs"] else "미달") if g["text_runs"] else "해당 없음"}')
    print()
print("도구 응답에 없는 숫자")
print()
for r in rows:
    bad = r["unmatched_numbers"] + r.get("unmatched_script_numbers", [])
    if bad:
        print(f'- q{r["q"]:02d} {r["cond"]} r{r["rep"]}: 도구 응답에 없는 숫자 {bad[:10]}')
