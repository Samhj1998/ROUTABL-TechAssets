# Step 4-B 공통 입력 배치

MacStudioui-MacStudio.local, 장치 ID `c377300b-a710-43a6-8169-f17e87175403`. 실제 환경 macOS 27.2 arm64, Python 3.9.6, SQLite 3.54.0. Step 4-A `SHA256SUMS`의 SHA-256은 `61c03ea7712ec85c171567fafa2ca513700d222d89ca9548261f9cf0eddb579e`이고 등록 25건 전부 일치했다. 매니페스트 SHA-256 `6edf8c96e783826f20ead03e72e3d61a201109bf00a285213b2e160669960031`도 확인했다.

B `/Users/yongho/121_CHATGPT_B_V01/implementation/input/`
C `/Users/yongho/121_CLAUDE_ISOLATED_V01/implementation/input/`

| 두 input에 동일 배치한 파일 | SHA-256 |
|---|---|
| `A_V15_QUERY_REFERENCE.py` | `10ecc1343744cfc0697ed5e6d634c6040231766f69a0bb33e861e63c36b98231` |
| `COMMON_ANALYSIS_PACKET_V01.md` | `d88a5a12e4a814105991fce95391079e7cdd22cddee0296d5ad33d3812c69bba` |
| `COMMON_TEST_SPEC.md` | `552bb8111f703048e657a26922954f2739156362efa37f54f5f7e5cf1e254f6d` |
| `FTS5_COMMON_FACTS_V01.md` | `db07e512bd349c6ff04d9bf898f94ff9ddde5f38f5bb9e5fb9c439b6921e50e1` |
| `SYNTHETIC_CORPUS_V01.json` | `840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b` |
| `SYNTHETIC_DEV_FIXTURE_V01.sqlite` | `d1b5045dd3a7669a076fe790bb038c4461e27a0062c16f0492afc2e78bd6b158` |
| `SYNTHETIC_DEV_V01.json` | `db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1` |

각 작업 루트가 없고 상위 경로에 심볼릭 링크가 없음을 확인 후 생성했다. 각 input은 0500, 7개 파일은 0400. 두 사본의 SHA-256을 배치 직후 확인했다. 쓰기 영역은 각 `src/`, `tests/`, `output/`이다. 작업용 DB는 해당 후보가 `tests/` 안에 만들도록 지시했다. 운영 회귀, 보류, 운영 DB 및 상대 결과는 배치에 포함하지 않았다. 검증 근거는 `STAGING_AND_COHORT_EVIDENCE.json`이다.
