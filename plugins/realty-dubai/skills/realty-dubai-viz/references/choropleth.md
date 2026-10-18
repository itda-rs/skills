# SVG 단계구분도 (get_boundaries)

1. `get_boundaries(places=[...])` 로 GeoJSON(WGS84 lon/lat)을 받는다. 값은 같은 곳에 대해 `compare_places` 또는 `screen_communities` 응답에서 가져온다(`place` 토큰으로 맞춘다).
2. 투영: 두바이는 범위가 좁아 등장방형으로 충분하다. `x = (lon - minLon) * cos(25.2°)`, `y = (maxLat - lat)` 를 viewBox 에 맞춰 늘린다. 이 계산은 그리기용이다.
3. 다각형(Polygon/MultiPolygon)을 `<path>` 로 그리고 `fill` 은 값 구간 색, 값이 null·표본 부족이면 `#46534e` + 빗금 없이 단색.
4. 각 다각형 중심(`properties.center`)에 이름과 값 라벨(`AED x,xxx/㎡ · n=…`)을 붙인다. 겹치면 이름만 남기고 표로 보낸다.
5. 범례: 색 구간과 경계값(게시값), "표본 부족" 칸.
6. 캡션: SKILL.md 절대 규칙 3 + `경계: DM Communities · 건물 점: © OpenStreetMap contributors`.
7. `unresolved` 가 있으면 지도 아래에 "경계 미게시: …" 로 적는다. 임장 지역(region)은 경계가 없다.
