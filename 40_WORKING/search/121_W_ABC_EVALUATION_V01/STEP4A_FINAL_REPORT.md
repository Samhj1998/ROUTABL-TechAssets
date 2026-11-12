# 121-W Step 4-A 종료 보고

장치 MacStudioui-MacStudio.local / `c377300b-a710-43a6-8169-f17e87175403`. 실행 환경 arm64 macOS 27.2, Python 3.9.6, SQLite 3.54.0. 결과 폴더 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_ABC_EVALUATION_V01/`.

| 검증 | 판정 | 결과 |
|---|---|---|
| B/C 최초 결과·운영 A 원본 보존 | PASS | B 11,781 B, C 9,786 B. 내용 해시 일치, B만 0600→0400. C 0400 유지. A 운영 소스·DB 해시 일치 |
| A 기존 증거 검증 | PASS | 기준선 SHA256SUMS 22건 일치. 역사적 A는 p95 207.52ms 및 기존 회귀 9/9. 새 후보 비교의 A는 동일 조건에서 재측정 |
| 독립안 비교 | PASS | 모두 FTS 후보+제목+원본 판정. B는 용어별 후보·스냅샷·보수적 폴백, C는 단일 OR MATCH와 SQL UNION 중심. 두 안의 성능 우열은 미판정 |
| FTS 구조·스냅샷 정합성 | PASS | 5,519 docs/ft 행이 rowid로 일대일 대응, 원본/FTS tags·content 불일치 0. `ft.path` 5,519행 모두 path+title |
| raw path 합집합, 짧은 검색어·별칭 강제 MATCH | FAIL | raw path 합집합은 개발 30건 중 18질의에서 54개 질의·행 누락. 2자·2자 별칭 표본 각 2행 누락 |
| rowid 합집합 개발 SQL 대조 | PASS | 합성 개발 30건 후보 누락 0. 원본 LIKE 재검사 및 동기화 검증 필요 |
| 축소 detail 가정 및 native 검사 단독 보장 | FAIL | detail=none/column에서 4자 phrase 오류. 고의적으로 FT 행을 지워도 native 검사 통과. docs와 ft 교차 검증 필요 |
| 갱신·삭제·이름 변경 | PASS(격리) | 함수 본문 보존한 합성 refresh 4세대에서 source 변경 반영과 docs/ft 정합성 확인. v1.1 단독 add의 동일 size/mtime 단축과 add-only rename은 stale 반례 |
| 선택적·다건 SQL 비용 대조 | PASS(측정) | 선택적 3행 p95 2.9182→0.4933ms. 다건 1,200행 2.0986→3.6045ms. 1,230행 합성 SQL 형태 단위 |
| 공통 게이트·구현 초안 | PASS | 공통 7파일 무결성. A 추출본이 개발 30×3 페이지 조합 90/90 일치. 평가자 보류 및 운영 백업은 패킷 밖 |
| 최종 기능·성능과 운영 복구 | NOT_TESTED | B/C 코드 미구현. 운영 회귀·보류 20·5배/10배·HTTP·동시 갱신·롤백 실행, 채택 목표 미판정 |

기존 A 평균 126.89ms, p50 117.66ms, 최대 277.12ms. SQLite 평균 115.70ms, Python/잔여 평균 10.60ms, R08 Python/잔여 59.26ms. A 합성 Recall@10/Precision@10/MRR@10/nDCG@10 0.80/0.16/0.80/0.80. 초성 0/10 FAIL은 보존한다. 운영 DB는 읽기 전용 연결과 SQLite Backup API를 사용했다. 운영 서비스 재시작 및 코드 변경, B/C 구현과 모델 호출, 공식 자산 변경은 0건이다.

## 증거 SHA-256

| 파일 | SHA-256 |
|---|---|
| ABC_ORIGINAL_FREEZE_VERIFY.md | `d6f7afb88b1a127dc168ca8e8506e5e10acba11adfef297ddc847ff87327b582` |
| BC_DESIGN_COMPARISON.md | `4a2bd63c6a165636e08ebaf96c53e400d2f3174f651326e8afd12d94d538cfdd` |
| FTS5_SCHEMA_AND_COVERAGE.md | `559cef825b508a7341014d152bf96f72494269a64d0656135dd774bcdf80e7ed` |
| FTS5_ISOLATED_FEASIBILITY.md | `8aac268e6f55a82479d4299052635c51f30ddb4ba2d3ab67ff4cbf2142a1a453` |
| FTS5_MEASURED_EVIDENCE.json | `976cc97d876e633bf6e8badcba04ea167c281c2eab3b3b9b980967d1f9b175ab` |
| FTS5_REFRESH_AND_PACKET_EVIDENCE.json | `e518e4a15bf0217ba9408001275ae1a70970caa4f686be5f7798c536c12eeb23` |
| FTS5_SQL_SHAPE_EVIDENCE.json | `309b01b06dbfe40bedcb1257aeee09f9fa2b653c529fc8c360e5cf5841b6687f` |
| COMMON_EVALUATION_GATES.md | `20575e406e15a231e3dcad16447558507b7ad7c51e8b8d85cd75ebeeb32301ca` |
| SYNTHETIC_SCALE_TEST_PLAN.md | `626aacd579d56394a4d95c823272dbd9103db3b236a7971953d17d6ed657b` |
| BC_IMPLEMENTATION_INPUT_MANIFEST.md | `6edf8c96e783826f20ead03e72e3d61a201109bf00a285213b2e160669960031` |
| STEP4B_IMPLEMENTATION_APPROVAL_REQUEST.md | `55aede559684f2061d73a692b639535efdd4490857f769b11853bcc16a3f8083` |

`SHA256SUMS`에서 본 보고서, 평가 사본, 재현 스크립트, 격리 DB 및 공통 초안의 전체 해시를 확인할 수 있다.

## 121 Chat에 복사할 검토 프롬프트

```text
121 Chat / Step 4-A 종료 검토와 Step 4-B 승인 범위 결정

MacStudioui-MacStudio.local / c377300b-a710-43a6-8169-f17e87175403에서 ASSET-SEARCH-01 v1.5의 B/C 동결본을 검증하고 FTS5 가능성을 격리 시험했습니다. B SHA c06379618720e1d982f0aae79d43d798775ea283659a8b6306ed0e5185ab8a8a, C SHA d534a406094e4e42d146fb0640d77e10b97667c72cf08452258f09244e0976c7입니다. 운영 소스 SHA 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d, DB SHA c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4가 보존됐습니다.

SQLite 3.54.0 운영 스냅샷에서 docs/ft 5,519행이 rowid로 일치했습니다. ft.path는 전부 경로+제목이었습니다. 개발 30질의에서 raw path 합집합은 18질의에서 54개 질의·행 쌍을 놓쳤고, rowid 합집합은 같은 표본에서 누락 0이었습니다. 짧은 확장어·NUL·지원 외 DDL·동기화 실패·MATCH 오류는 기존 LIKE 경로로 보내야 합니다. native 검사 외 docs/ft 교차검사를 적용합니다. 격리 갱신/삭제/rename은 PASS입니다. 선택적 3행 SQL은 빨라졌고 다건 1,200행 SQL은 느려졌습니다. 운영 회귀, 보류 및 후보 성능은 NOT_TESTED입니다.

증거 경로 /Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_ABC_EVALUATION_V01/
공통 패킷의 7개 경로·크기·해시는 BC_IMPLEMENTATION_INPUT_MANIFEST.md (6edf8c96e783826f20ead03e72e3d61a201109bf00a285213b2e160669960031)로 검증합니다.
게이트는 COMMON_EVALUATION_GATES.md (20575e406e15a231e3dcad16447558507b7ad7c51e8b8d85cd75ebeeb32301ca)입니다. 운영 9/9, 개발 30·보류 20 회귀 0, 정확도 비악화, 후보 누락 0, 갱신 정합성을 선행합니다. 혼합/선택적 p95 각각 20%/30% 개선, 짧은·다건·폴백 10% 이내 악화, 생성·갱신 각 10% 원칙, 저장 5%를 목표로 합니다.

새 B/C 구현 세션에는 동일한 7개만 제공합니다. 후보 경로는 /Users/yongho/121_CHATGPT_B_V01/implementation/ 및 /Users/yongho/121_CLAUDE_ISOLATED_V01/implementation/입니다. 기존 인덱스 재사용, 후보 추출과 원본 판정, 스냅샷·세대 검증·폴백·계측 및 합성 개발 시험을 제안합니다. 상대 분석·코드, 운영 DB/백업, 실제 회귀 질의, 보류는 평가자 전용입니다. Claude는 기존 Pro와 Usage credits 비활성 조건을 재확인하며 추가 과금은 금지합니다.

STEP4B_IMPLEMENTATION_APPROVAL_REQUEST.md (55aede559684f2061d73a692b639535efdd4490857f769b11853bcc16a3f8083)에 따라 ① 두 세션 배치·제공 범위 ② 코드·시험 범위와 동결 방법 ③ 실행 전 혼합·선택도 코호트 ④ 동결 후 공통 시험 승인 경계를 확정해 주세요. 운영 원본·서비스·공식대장 변경은 제외합니다.
```
