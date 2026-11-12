# Digitopia MVL-01 검증서

검증 시각 2026-11-08T06:59:30+09:00.
MacStudioui-MacStudio.local, Desktop Commander Remote, Mac의 Python 및 SQLite. 작업 범위는 MVL-01 신규 격리 폴더와 원본 읽기 확인이다.

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 실제 대장·원본·운영 DB의 제공값 검증 | PASS | ORIGIN_PROOF.json, PROTECTED_SCOPE.json |
| v0.6 기반 검색과 격리 검색 기능 동등성 | PASS | LEGACY_REGRESSION.json. 9개 검색의 전체 결과에서 신규 origin 필드만 제외하고 정확 비교 |
| 기능·부정·환류 시험 | PASS 14/14 | TEST_RESULTS_INITIAL.json 10/10, TEST_RESULTS_FINAL.json 4/4 |
| 검색 DB 무결성 | PASS | SQLite quick_check. 기존 docs 5519, 격리 메타데이터 추가 후 5527, 기존 explicit-local 2 |
| 초기 인계 및 환류 재인계 | PASS | 7건과 8건. Markdown·JSON 재생성과 파일 결과 일치. FEEDBACK_SEARCH.json |
| 보호 원본 전후 대조 | PASS | SHA-256 82개, 파일·디렉터리 메타데이터 557개. 비교 범위 안에서 차이 0 |
| 독립 수신·활용 | NOT_TESTED | INDEPENDENT_RECEIVER_PROMPT.md |
| 11월 8일 조사 B, 실제 백업·복원, 운영 배포 | 별도 범위 | 이번 격리 시험의 성공 근거에 포함하지 않음 |
| First Ignition / 최소 완성판 | PARTIAL / PARTIAL | ASSESSMENT.md. 독립 AI 실제 활용이 P1 |

대장 정식 변경과 v043 전환 없이 검색 격리판을 CLI로 제공한다. 최신 대장 판본이 바뀌면 승인 해시의 재검토가 필요하다. 기본 인계는 고정 자료의 검증 메타데이터를 쓰고 사용자 추가 원본을 자동 제출하지 않는다. 운영 DB 복사본은 로컬 전용 자료이며 전달 후보에 포함되지 않는다. 저장소 전체 전수 바이트 검사 및 개인정보 전수 감사는 이 결과에서 제외한다.

전체 생성 파일의 SHA-256은 SHA256SUMS에 수록한다. 목록 파일 자체의 SHA-256은 Work 결과에 별도 기재한다.
