# B 최초 구현 동결

독립 `121-B-W`에서 완료 보고를 받아 같은 Mac Studio에서 별도 검산했다. 경로 `/Users/yongho/121_CHATGPT_B_V01/implementation/`. 구현 루트에서 `/usr/bin/shasum -a 256 -c output/SHA256SUMS` 종료 코드 0, 10/10 일치. B 보고의 주요 7개 SHA가 모두 동일했다. 121-W는 소스나 시험을 수정하거나 다시 실행하지 않았다.

| 상대 경로 | SHA-256 |
|---|---|
| src/search_b.py | `f46f64e2479a331c6bd6822f7b0b41af2fbceeab801bb27ad679dce108d1950d` |
| tests/test_search_b.py | `befd28ddf68045e6a16bb8e1452a153a64a4d3d207a645a4b15621aad91b5299` |
| output/IMPLEMENTATION_REPORT.md | `a99497b2394791e533afff75581d363038ed92804b13f2b18342335b5e019f09` |
| output/DEV_TEST_REPORT.md | `290b8d689795aab66ceebf94b3b0cd7b5ccf2a98afa92b3fd3608434ca07ef12` |
| output/CHANGE_MANIFEST.md | `3cf263026ca863012669a9371fcfca9b2cb2fc959995e583c279d2fdf266cfcb` |
| output/dev_run_03.jsonl | `6c8a76f6ef8b93d282fa301a4b59024e56abe5a125039dee4600f21af6aadf83` |
| output/SHA256SUMS | `70ec00dfe861be12aa075ec0011dd9bab58dafeae1d6f3829f9b441d3f795a28` |

파일 단위 추가 동결 `B_FREEZE_ARTIFACTS.json` SHA-256 `36526cb7ae127db0b483727a1732d66f3752a810beda5af9d5b300cde84a18ab`. 작업용 DB와 초기 실패 증거까지 총 36개 항목을 검산하고, 최초 파일 0400 및 작업 하위 디렉터리 0500으로 고정했다.

개발 결과는 독립 B의 실행 증거 기준 공개 객체 30/30, 후보 누락 0, 경계·무결성 36/36 PASS. A와 B의 Recall/Precision/MRR/nDCG@10은 각각 0.800/0.160/0.800/0.800. 초성 6개는 공통으로 정답 기대 미충족. 시험 소스의 초기 실패와 수정 기록을 보존했다. B 후보 소스 자체는 세 실행에서 동일하다고 보고됐다. 세대 검증에서 메모리 DB 백업과 FTS 무결성 검사 비용이 있어 공식 평가의 새 연결 및 재사용 연결 계층을 분리한다.

경로 규약 **FAIL**. B가 만든 합성 작업 DB 21건이 `output/` 아래에 있었다. 승인 구조는 `tests/` 아래 배치다. 요청 범위의 후보 트리 안에 있었으며, 현재 증거 경로는 최초 동결 상태로 보존했다. 이후 재현에서는 승인된 `tests/` 아래의 새 격리 사본을 사용한다. 운영·보류·공식 성능 시험은 NOT_TESTED.
