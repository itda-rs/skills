---
name: realty-dubai-viz
description: Use when visualizing Dubai real-estate data from the "부동산 실거래" (realty) MCP tools — charts, tables, maps, comparisons, trends, 임장 one-pagers. 두바이 시세·실거래·비교·추세·지도를 그려 달라는 요청이나 realty MCP 도구 결과(get_market, compare_places, screen_communities, get_monthly_trend, get_boundaries, search_transactions)를 그림으로 만들 때 쓴다.
---

# 두바이 실거래 시각화 (realty MCP)

realty MCP 가 **숫자**를 주고, 이 스킬은 **그리는 법**을 정한다. 그림은 값을 바꾸지 않는 표현일 뿐이다.

## 절대 규칙
1. **숫자는 도구 응답 값만 쓴다.** 중앙값·평균·비율·합계를 새로 계산하지 않는다. 표시용 반올림만 한다.
   - 예외: 축 범위·막대 길이 같은 *그리기용* 좌표 계산은 해도 된다. 그 결과를 숫자로 적지 않는다.
2. **값이 null 이거나 `low_sample`=1/true 이면 "표본 부족"** 으로 그린다: 회색(#46534e) 칸·빈 막대·끊긴 선. 다른 기간·지역 값으로 채우거나 보간하지 않는다. n 은 그대로 보인다.
3. **모든 그림에 캡션**: `출처: DLD 실거래(data.dubai, <source.sales_dataset>) · 기준일 <source.data_as_of> · n=<값> · 기간 <filters.months>개월` + "두바이 정부 공식 서비스 아님 · 투자 권유 아님". 지도는 `attribution`(DM Communities 경계 · © OpenStreetMap contributors)도 적는다.
4. **분양(offplan)과 준공(ready)은 나눠 그린다.** `registration=all` 이면 제목에 "분양·준공 합산"이라고 적는다.
5. **실거래·임대·레이어(관리비·연식 등)·사용자 호가는 한 축·한 열에 섞지 않는다.** 감정가가 오면 "감정가"로 따로 그린다.
6. `unavailable_dimensions` 에 있는 차원은 "게시되지 않음"으로 쓰고 다른 값으로 대신하지 않는다.
7. **투자 판단 표현 금지**: "싸다·저평가·추천·사라" 대신 "㎡당 중앙값이 낮다·변화율 +x%"처럼 게시값만 말한다. 순위는 사용자가 정한 정렬 기준임을 밝힌다.
8. 그린 뒤 **자체 대조**: 그림·표에 적힌 숫자를 도구 응답과 하나씩 맞춰 보고, 다르면 고친다. 응답 끝에 "숫자 대조: N개 일치" 한 줄을 남긴다.

## 어떤 도구 → 어떤 그림
- `compare_places` / `get_market` 여러 곳 → **가로 막대**: 막대 = `med_aed_sqm`, 가는 선 = `p25_aed_sqm`~`p75_aed_sqm`, 막대 끝 라벨 `n=…`. 분양/준공은 색이 아닌 **나란한 두 막대**로.
- `get_monthly_trend` → **선 그래프**: `available=false` 또는 null 인 달은 선을 끊고 회색 점 + "표본 부족". `partial_days` 가 있는 마지막 달은 점선 + "부분 월(1일~기준일)".
- `screen_communities` → **표 먼저**, 그다음 막대. 탈락 수(`excluded_low_sample`, `excluded_no_value`)를 표 아래에 적는다.
- `get_boundaries` (+ 같은 곳의 값) → **SVG 단계구분도**. `references/choropleth.md` 를 따른다. 외부 타일·폰트·CDN 쓰지 않는다.
- `search_transactions` → **표**(거래 ID·날짜·면적·가격·㎡당). 최대 20행. 원자료를 통째로 옮기지 않는다(재배포 금지).
- 임장 한 장 요약 → `references/one-pager.md`.

## 색 (웹 지도 realty.rs.itda.work 와 같음)
- 순차(단가·수익률): `#dcebd7` → `#a6c9ad` → `#598f76` → `#23594b` (4구간). 표본 부족·값 없음 `#46534e`.
- 변화율(발산): 하락 `#386fa4` · 보합 `#edf0e9` · 상승 `#b64c39`.
- 구간 경계는 응답에 있는 p25·중앙값·p75 등 **게시값**을 쓴다. 응답에 없으면 4분위를 새로 계산하지 말고 "구간: 이 그림의 값 범위를 4등분(그리기용)"이라고 캡션에 밝힌다.

## 형식
- claude.ai: HTML/SVG 또는 React 아티팩트. 외부 리소스 없이 자체 완결.
- Claude Code·Codex: 자체 완결 HTML 파일 하나(인라인 SVG). 저장 경로를 알려 준다.
- 텍스트만 되는 곳: 마크다운 표 + 출처 각주.
- 단위: AED/㎡ 기본, 필요하면 AED/sqft(`med_aed_sqft`) 병기. 통화 기호 대신 "AED".
- 숫자 등장 효과(count-up)·3D 막대·이중 축 쓰지 않는다.

## 다른 AI 로 넘길 때(인포그래픽 등)
쓴 숫자를 그대로 옮긴 마크다운 표 한 장에 `출처 · 기준일 · n` 열을 넣고, 맨 아래에 "실거래 등기 기준 · 호가 아님 · 투자 권유 아님 · 값 변경 금지"를 적는다.
