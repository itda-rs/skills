#!/usr/bin/env python3
"""Claude Code 헤드리스로 스킬 없음/있음 A/B 를 돌리고 판정 재료를 모은다.

사용: python3 evals/run_claude_code.py --q 1 --cond skill --rep 1 --out runs/
- cond=base  : 플러그인 없이(MCP 커넥터만)
- cond=skill : --plugin-dir plugins/realty-dubai
각 실행 폴더에 stream.jsonl, tool_results.json(도구 응답 원문), 결과 HTML/마크다운, numbers.json(대조)을 남긴다.
주의: realty MCP 호출 한도(1분 20 / 5시간 150 / 24시간 400, 사용자별). 한 실행에 보통 2~6회 호출.
"""
import argparse, json, re, subprocess, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUESTIONS = [l.split(". ", 1)[1].strip() for l in (ROOT / "evals/questions.md").read_text().splitlines()
             if re.match(r"^\d+\. ", l)]
SUFFIX = ("\n\n결과는 현재 폴더에 자체 완결 HTML 파일 하나(chart.html)로 저장하고, 마지막에 파일 경로와 핵심 숫자를 짧게 알려 줘. "
          "두바이 부동산 데이터는 연결된 '부동산 실거래' MCP 도구를 써.")


def numbers(text):
    out = set()
    for m in re.findall(r"(?<![\w.])-?\d[\d,]*\.?\d*", text):
        v = m.replace(",", "")
        try:
            f = float(v)
        except ValueError:
            continue
        if abs(f) >= 10:  # 작은 수(색 인덱스·연도 일부 등) 제외
            out.add(round(f, 1))
    return out


def tool_numbers(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values():
            tool_numbers(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            tool_numbers(v, acc)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        acc.add(round(float(obj), 1))
    elif isinstance(obj, str):
        acc |= numbers(obj)
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--cond", choices=["base", "skill"], required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--out", default=str(ROOT / "evals/runs"))
    ap.add_argument("--model", default=None)
    ap.add_argument("--parse-only", action="store_true", help="이미 있는 stream.jsonl 만 다시 판정")
    ap.add_argument("--mcp-config", default=None,
                    help="로컬 MCP 설정 JSON(서버 이름 realty). 주면 --strict-mcp-config 로 이것만 쓴다(운영 한도 우회, 평가 전용)")
    a = ap.parse_args()
    run = pathlib.Path(a.out) / f"q{a.q:02d}-{a.cond}-r{a.rep}"
    run.mkdir(parents=True, exist_ok=True)
    prefix = "mcp__realty__" if a.mcp_config else "mcp__claude_ai_2__"
    cmd = ["claude", "-p", QUESTIONS[a.q - 1] + SUFFIX, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "acceptEdits", "--allowedTools", f"Write,Read,Bash(ls:*),{prefix}*"]
    if a.mcp_config:
        cmd += ["--strict-mcp-config", "--mcp-config", a.mcp_config]
    if a.cond == "skill":
        cmd += ["--plugin-dir", str(ROOT / "plugins/realty-dubai")]
    if a.model:
        cmd += ["--model", a.model]
    t0 = time.time()
    cost = None
    if not a.parse_only:
        with open(run / "stream.jsonl", "w") as f:
            subprocess.run(cmd, cwd=run, stdout=f, stderr=open(run / "stderr.txt", "w"), timeout=900)
    tool_calls, tool_results, final = [], [], ""
    uses = {}  # tool_use_id -> (name, input)
    src_texts = []  # 숫자 출처로 인정하는 텍스트: MCP 응답 + 파일로 넘친 MCP 응답을 다시 읽은 결과
    for line in open(run / "stream.jsonl"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = d.get("message") if isinstance(d.get("message"), dict) else {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                tool_calls.append({"name": c["name"], "input": c.get("input")})
                uses[c.get("id")] = (c["name"], json.dumps(c.get("input"), ensure_ascii=False))
            if c.get("type") == "tool_result":
                body = c.get("content")
                if isinstance(body, list):
                    body = "".join(x.get("text", "") for x in body if isinstance(x, dict))
                tool_results.append(body)
                name, inp = uses.get(c.get("tool_use_id"), ("", ""))
                if name.startswith(prefix) or ("tool-results" in inp and name in ("Read", "Bash")):
                    src_texts.append(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False))
        if d.get("type") == "result":
            final = d.get("result", "")
            cost = d.get("total_cost_usd")
    mcp_calls = [t for t in tool_calls if t["name"].startswith(prefix)]
    other_mcp = sorted({t["name"].split("__")[1] for t in tool_calls
                        if t["name"].startswith("mcp__") and not t["name"].startswith(prefix)})
    mcp_results = []
    for body in tool_results:
        try:
            mcp_results.append(json.loads(body))
        except (json.JSONDecodeError, TypeError):
            pass
    src = set()
    for r in mcp_results:
        tool_numbers(r, src)
    for t in src_texts:
        src |= numbers(t)
        src |= {round(float(m), 1) for m in re.findall(r"(?<![\w.])-?\d+\.\d+", t)}
    rate_limited = sum(bool(re.search(r"호출 한도|rate.?limit|Too Many Requests|\b429\b(?!\d|,|\.)(?=\D{0,20}(error|오류|Too))", t, re.I)) for t in src_texts)
    html = (run / "chart.html").read_text() if (run / "chart.html").exists() else ""
    visible = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html)
    visible = re.sub(r"<[^>]+>", " ", visible)
    shown = numbers(visible)
    # 그리기 좌표가 아닌 '보이는 텍스트'의 수만 대조. 반올림 표시(k, 정수) 허용.
    def matched(x):
        return any(abs(x - s) <= max(0.51, abs(s) * 0.0005) for s in src) or \
               any(abs(x * 1000 - s) <= 50 for s in src) or \
               any(abs(x * 10000 - s) <= 5000 for s in src)  # 25.4k, 260만 같은 표기
    # 축 눈금: 같은 간격으로 3개 이상 늘어선 정수열(간격이 500·1000 등의 배수)은 그리기용이다.
    def ticks(vals):
        ints = sorted(v for v in vals if v == int(v) and v % 100 == 0)
        out = set()
        for step in (100, 250, 500, 1000, 2000, 2500, 5000, 8000, 10000):
            run = [v for v in ints if v % step == 0]
            for v in run:
                if v + step in run and (v + 2 * step in run or v - step in run):
                    out |= {v, v + step}
                    if v + 2 * step in run: out.add(v + 2 * step)
                    if v - step in run: out.add(v - step)
        return out
    tick_vals = ticks(shown)
    shown = shown - tick_vals
    # 순위·목록 번호 같은 작은 정수(≤50)는 대조에서 뺀다.
    unmatched = sorted(x for x in shown if not matched(x) and not (x == int(x) and abs(x) <= 50))
    # 그림을 JS 로 그리는 경우: 스크립트 안 데이터 리터럴(소수 또는 1000 이상)도 대조한다.
    script = " ".join(re.findall(r"<script[\s\S]*?</script>", html))
    script_vals = set()
    script = re.sub(r"\b(?:r|W|H|L|R|w|h|width|height|rowH|barH|pad\w*|cx|cy|x|y|dx|dy|size|opacity|stroke\w*|font\w*)\s*[:=]\s*\"?-?\d+(?:\.\d+)?", " ", script)
    script = script.replace("111.32", " ").replace("111.320", " ")  # 위도 1도 ≈ 111.32 km (축척 막대)
    for m in re.findall(r"(?<![\w.#])-?\d+(?:\.\d+)?(?![\w])", script):
        f = float(m)
        if "." in m or abs(f) >= 1000:
            script_vals.add(round(f, 1))
    # 축 눈금(1000 의 배수 정수)은 그리기용이라 대조에서 뺀다.
    unmatched_script = sorted(x for x in script_vals if not matched(x) and not (x == int(x) and int(x) % 1000 == 0))
    report = {
        "q": a.q, "cond": a.cond, "rep": a.rep, "seconds": round(time.time() - t0),
        "skill_tool_calls": [t for t in tool_calls if t["name"] == "Skill"],
        "mcp_calls": [t["name"].split("__")[-1] for t in mcp_calls],
        "html": bool(html), "shown_numbers": len(shown), "unmatched_numbers": unmatched[:60],
        "script_numbers": len(script_vals), "unmatched_script_numbers": unmatched_script[:60],
        "caption_incl_script": {k: bool(re.search(p, visible + " " + script)) for k, p in
                    {"source": r"DLD|data\.dubai|Dubai Land", "as_of": r"기준일|as of|2026-10-\d\d",
                     "n": r"\bn\s*=|건수|표본", "notice": r"공식 서비스|official"}.items()},
        "caption": {k: bool(re.search(p, visible)) for k, p in
                    {"source": r"DLD|data\.dubai|Dubai Land", "as_of": r"기준일|as of|2026-10-\d\d",
                     "n": r"\bn\s*=|건수|표본", "notice": r"공식 서비스|official"}.items()},
        "low_sample_marked": bool(re.search(r"표본 부족|low.?sample", visible, re.I)),
        "split": bool(re.search(r"분양|오프플랜|off-?plan", visible, re.I) and re.search(r"준공|ready", visible, re.I)) or
                 bool(re.search(r"합산", visible)),
        # 엄격: 분양·준공을 실제로 따로 조회했거나(registration=offplan/ready 호출) 응답 자체가 둘로 나뉘어 왔다.
        "split_strict": any(re.search(r'"registration":\s*"(offplan|ready)"', json.dumps(t.get("input") or {})) for t in mcp_calls)
                        or any(isinstance(r, dict) and re.search(r'"(offplan|ready)":\s*\{', json.dumps(r)) for r in mcp_results),
        "other_mcp_servers": other_mcp,
        "cost_usd": cost, "rate_limited_results": rate_limited,
        "raw_rows_in_html": html.count('"psm"') + len(re.findall(r"<tr>", html)),
        "final": final[:800],
    }
    (run / "tool_results.json").write_text(json.dumps(mcp_results, ensure_ascii=False, indent=1))
    (run / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "final"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
