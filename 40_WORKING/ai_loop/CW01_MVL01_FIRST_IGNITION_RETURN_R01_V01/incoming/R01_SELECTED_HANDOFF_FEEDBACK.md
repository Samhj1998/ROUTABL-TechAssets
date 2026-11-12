# R01 선택 인계 개선 환류 후보

자산 ID MVL-USER-R01-SELECTED-HANDOFF, 판본 1.0. 이 문서는 격리 DB의 후보 등록용이다.

## 이전 120-2-W 기준

기존 MVL-01의 인계, 실행 안내, 검색·검증 코드를 R01이 개발에 활용했다. 입력 계보는 R01 INPUT_SHA256.json (34ee6452518dd27a5c930b1163570f818a62ddb1d751c831fabc4de080f3a87c)에 기록됐다. 변경 전 mvl.py SHA-256은 6aa94e2c46aea8b70313952dba7440c71696542d2fc64413b5cb7cb7f9b3b1b3다. 기존 기술자산의 등록, 출처 검증, v1.5 검색과 기본 인계 계약을 재사용했다.

## 독립 Work R01 개발 및 시험

R01은 반복 가능한 --asset-id를 추가했다. 기존 SQLite 등록·색인 행을 정확한 ID로 조회하고 기존 원본 검증을 사용한다. 같은 바이트를 가진 서로 다른 자산도 지정 순서를 유지한다. 요청한 후보 중 하나라도 실패하면 표준 출력 없이 종료 코드 1로 종료한다. 인계에는 검증된 메타데이터만 사용한다.

R01 최초 합성 시험은 provenance_crosswalk 누락으로 오류 20건, 스텁 수정 후 20/20 PASS를 보고했다. 원래 로그는 R01 원본 및 synthetic/TEST_RESULTS_ATTEMPT_01.txt (906e75ec3a83c090796e23267dc0544b45ea2c8876b9bed07255b5e53348aa80)에 보존했다.

## 이번 120-2-W의 독립 재검증

SELECTED_HANDOFF.patch (b234c55c3f30a17f44d1d4a253a648de26b206374f6e05e0c3ebc577d51ebdc8)는 mvl.py 한 파일만 변경한다. 패치 결과 SHA-256 e8f3b458475e5d783e98bf0f2b1ebe6ccc2235a4355df70b44aea59ef1ab8fdd는 R01 후보와 일치했다. Python 3.9.6에서 합성 시험 20/20 PASS, 종료 코드 0. 세션의 직접 시험은 synthetic/REVALIDATION_TEST_RESULTS.txt와 R01_REVALIDATION.txt에 기록했다.

실제 MVL-01 SQLite의 격리 복사본에서 검색 9/9가 기준 코드 및 이전 순위·건수 기록과 일치했다. 기본 인계 initial/final은 금지된 운영 검색 원본 ASSET-SEARCH-V15-SERVICE에서 차단됐다. 상속된 MVL01-FEEDBACK의 등록 경로도 신규 격리 ROOT의 기대 경로와 다르다. 기본·선택 인계의 실제 성공 판정은 별도로 기록하며 이 문서가 이를 증명하지 않는다.

## 재현 및 증거

합성 재현은 이 검증 폴더의 synthetic/에서 실행한다.

    LC_ALL=en_US.UTF-8 /usr/bin/python3 -E -s -B -m unittest -v test_selected_handoff

실제 격리 검증은 검증 폴더에서 scope_runner.py를 통해 실행한다. 승인 경로만 열며 운영 원본은 열지 않는다.

    /usr/bin/python3 -E -s -B scope_runner.py mvl.py search MVL-USER-R01-SELECTED-HANDOFF
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py handoff final --asset-id MVL-USER-R01-SELECTED-HANDOFF

- R01_REVALIDATION.txt SHA-256 b65fade044757d14f1dce83fb724f3a3cbc665c080e6900322d09614606df048
- BASELINE_COMPARISON.json SHA-256 b772852d6a9401c18da05245a24ec08983eea23083c688fa78cec828a696503a
- 후속 등록·재검색·인계 증거는 ROUND_TRIP_EVIDENCE.json에서 확인한다.
