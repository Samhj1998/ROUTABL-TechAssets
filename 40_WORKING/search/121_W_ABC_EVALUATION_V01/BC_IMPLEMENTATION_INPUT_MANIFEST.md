# B/C 구현 공통 입력 매니페스트 v01

Mac Studio 로컬 초안만 준비했다. 경로 기준 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_ABC_EVALUATION_V01/IMPLEMENTATION_COMMON_DRAFT/`. 아래는 이 폴더의 같은 바이트를 두 세션에 승인 후 각각 배치할 후보 7건이다. 기존 4건은 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_BASELINE_V01/`의 원본을 사용했다.

| 자산 | 파일명 | 바이트 | SHA-256 | 목적 |
|---|---|---:|---|---|
| 121-M01 v01 | COMMON_ANALYSIS_PACKET_V01.md | 1,944 | `d88a5a12e4a814105991fce95391079e7cdd22cddee0296d5ad33d3812c69bba` | 현행 흐름·계약 |
| 121-M02 v01 | SYNTHETIC_CORPUS_V01.json | 1,097,578 | `840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b` | 1,230행·합성 별칭·crosswalk |
| 121-M03 v01 | SYNTHETIC_DEV_V01.json | 14,829 | `db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1` | 공개 개발 30·qrels |
| 121-M04 v01 | COMMON_TEST_SPEC.md | 3,471 | `552bb8111f703048e657a26922954f2739156362efa37f54f5f7e5cf1e254f6d` | 기존 공통 평가 규격 |
| ASSET-SEARCH-01 v1.5 extract | A_V15_QUERY_REFERENCE.py | 7,811 | `10ecc1343744cfc0697ed5e6d634c6040231766f69a0bb33e861e63c36b98231` | v1.5 원문 query, relevant, safe_like, basename, kind, MAIN_PROJECTS/SCOPE 및 합성 바인딩 |
| 121-M05 v01 | SYNTHETIC_DEV_FIXTURE_V01.sqlite | 3,325,952 | `d1b5045dd3a7669a076fe790bb038c4461e27a0062c16f0492afc2e78bd6b158` | 동일 스키마·실제 legacy add를 거친 1배 합성 DB |
| 121-M06 v01 | FTS5_COMMON_FACTS_V01.md | 1,922 | `db07e512bd349c6ff04d9bf898f94ff9ddde5f38f5bb9e5fb9c439b6921e50e1` | 검증한 데이터 구조, 폴백 조건, 계약·채택 기준 |

추출 원본은 `/Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_5_service.py` 22,823 B, SHA `55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d`. 34–36, 39, 86–99, 101–102, 104–106, 108–166, 168–247행의 상수와 함수 본문을 원문 그대로 취했다. A 참조는 합성 데이터에만 연결한다. 운영 경로·서비스 시작 코드·credential 파일·실제 별칭/검증 매핑을 제외했다. 공통 4건과 추출 소스의 키/토큰·비밀 대입·이메일·전화·주민번호형 정규식 검사에서 탐지 0건. 검사는 알려진 패턴에 한정된다. SQLite는 합성 JSON에서만 생성했고 manual 0행이다. 공개 30질의에서 역사적 fixture 빌드와 메타데이터 일부가 다르지만 3개 페이지 조합의 A 반환 객체 90/90이 일치했다.

## 승인 후 동일 배치

- B `/Users/yongho/121_CHATGPT_B_V01/implementation/`
- C `/Users/yongho/121_CLAUDE_ISOLATED_V01/implementation/`

각 경로 아래 `input/`에는 위 파일만 0400, `src/`, `tests/`, `output/`은 해당 세션 전용 쓰기 영역을 제안한다. 작업이 필요한 DB는 합성 입력 사본을 `tests/`에 복제한다. 원본 A 추출본, 합성 fixture, 입력 매니페스트는 봉인한다. 기존 경로 충돌 및 심볼릭 링크 확인 후 동일 이름·동일 해시를 비교한다. 독립 분석 원문이나 상대 안 관련 결론, 운영 원본 DB·백업, 실제 회귀 질의·결과, 보류 20건 및 생성기는 공통 입력에서 제외한다.

후속 구현의 일반 변경 범위는 후보 SQL/키 조회, 동일 읽기 세대·건강 신호·폴백과 평가 계측이다. 기본 계획은 운영 DDL, 서비스, 갱신 로직의 변경 없이 existing ft를 재사용하는 것이다. 전체 v1.5 서비스 및 legacy 모듈 배포는 후속 검토 사항이다. 갱신/동기화와 운영 통합 테스트는 평가자가 실행한다.
