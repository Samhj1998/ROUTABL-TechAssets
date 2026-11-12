# A/B/C 원본 동결 및 보존 확인

MacStudioui-MacStudio.local / `c377300b-a710-43a6-8169-f17e87175403`. A는 ASSET-SEARCH-01 v1.5, B/C는 최초 독립 분석 문서다.

| 대상 | 절대경로 | 바이트 | SHA-256 | 검증 |
|---|---|---:|---|---|
| B | `/Users/yongho/121_CHATGPT_B_V01/output/ANALYSIS_B.md` | 11,781 | `c06379618720e1d982f0aae79d43d798775ea283659a8b6306ed0e5185ab8a8a` | PASS. 0600→0400 전후 해시 일치 |
| C | `/Users/yongho/121_CLAUDE_ISOLATED_V01/output/ANALYSIS_C.md` | 9,786 | `d534a406094e4e42d146fb0640d77e10b97667c72cf08452258f09244e0976c7` | PASS. 0400 |
| A 소스 | `/Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_5_service.py` | 22,823 | `55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d` | PASS. 읽기 전용 재검산 |
| A DB | `/Users/yongho/Library/Application Support/ROUTABL-AssetSearch/assets_v1_5.sqlite` | 86,417,408 | `c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4` | PASS. 읽기 전용 재검산 |

B/C 비교에는 이 폴더의 `EVAL_ANALYSIS_B.md`, `EVAL_ANALYSIS_C.md`를 사용했다. 각 사본은 원본과 바이트·SHA-256이 일치하며 0400이다. 변경된 원본 메타데이터는 승인된 B 모드 1건이다.

기준선 폴더 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_BASELINE_V01/`의 `SHA256SUMS`는 `546c4bc1bdd5db3072a108b66aacc5b48ea52ef36461758ca6339ca7b4969642`이고 22개 항목 일치. 과거 A 수치는 이 기준선의 기록이다. `FTS5_MEASURED_EVIDENCE.json`은 운영 원본 DB와 별도의 평가자 전용 SQLite 백업을 구분한다. 백업 후 운영 원본 해시는 위 기준과 일치했다.
