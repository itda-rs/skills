# itda-rs/skills

잇다 rs 서비스용 Agent Skills 마켓플레이스입니다. **데이터는 없고 규칙과 틀만** 담습니다.

## 플러그인
- `realty-dubai` — 두바이 실거래 MCP(「부동산 실거래」, `https://realty.rs.itda.work/mcp`) 결과를 출처·기준일·표본 수(n)를 지키며 표·차트·SVG 지도로 그리는 스킬 `realty-dubai-viz`.

## 설치
- **Claude Code**
  ```
  /plugin marketplace add itda-rs/skills
  /plugin install realty-dubai@itda-rs
  ```
  MCP 연결(OAuth 로그인)이 함께 등록됩니다.
- **Codex / ChatGPT Work**: 이 저장소를 Git 마켓플레이스로 추가한 뒤 `realty-dubai` 를 설치합니다.
- **claude.ai**: [Releases](https://github.com/itda-rs/skills/releases) 에서 `realty-dubai-viz.zip` 을 받아 설정 → 기능(Skills)에 올립니다. 커넥터는 https://realty.rs.itda.work/ 안내대로 따로 연결합니다.

## 검증
릴리스마다 `evals/` 의 고정 질문을 스킬 없음/있음으로 돌려 비교합니다. 결과표는 Release 노트에 붙입니다.

## 고지
- 데이터: Dubai Land Department 공개 데이터(data.dubai). 이 저장소와 서비스는 두바이 정부 공식 서비스가 아닙니다.
- 실거래 등기 기준이며 호가·감정가가 아닙니다. 투자 권유가 아닙니다.

라이선스: MIT
