# Digitopia MVL-01 First Ignition R01 반환 검증

검증 시각 2026-11-08T08:18:47+09:00 KST. 장치 MacStudioui-MacStudio.local, ID c377300b-a710-43a6-8169-f17e87175403.
신규 격리 폴더 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_RETURN_R01_V01

## 판정

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| R01 결과 재검증 | PASS | 수신 파일 13개 직접 해시 일치. 패치 한 파일을 바이트 단위로 재현. 합성 안전 시험 20/20, 종료 코드 0. |
| 환류 순환 검증 | NOT_TESTED (완주 기준) | 등록·재검색·선택 ID 직접 검증은 PASS. 실제 기본·선택 인계의 성공 결과는 승인 경계에서 차단. |
| First Ignition 최소 완성판 | PARTIAL | 독립 개발 및 재검증 증거 확보. 실제 기본 제외·선택 포함 인계 및 전달 해시 대조 미검증. |

## 작업의 출처

- 기존 120-2-W는 MVL-01 검색·대장 검증·고정 인계·기초 환류를 구축했고 독립 수신은 당시 미검증으로 남겼다.
- 독립 Work R01은 해당 자료를 활용해 반복 가능한 --asset-id 정확 선택을 개발했다. 첫 합성 시험은 provenance_crosswalk 스텁 누락으로 오류 20건이었다. 스텁 수정 후 20/20을 보고했다. 처음 실패한 원문을 synthetic/TEST_RESULTS_ATTEMPT_01.txt에 보존했다.
- 이번 120-2-W가 직접 재현한 패치와 시험, 실제 격리 DB 등록 및 재검색, 인계 차단 결과는 아래 증거에 기록했다.

## 직접 재검증

기준 mvl.py 및 R01 mvl_original.py SHA-256 6aa94e2c46aea8b70313952dba7440c71696542d2fc64413b5cb7cb7f9b3b1b3. 적용한 패치 SHA-256 b234c55c3f30a17f44d1d4a253a648de26b206374f6e05e0c3ebc577d51ebdc8. 재현 mvl.py SHA-256 e8f3b458475e5d783e98bf0f2b1ebe6ccc2235a4355df70b44aea59ef1ab8fdd. R01 후보와 바이트 일치.
Python 3.9.6. synthetic/에서 LC_ALL=en_US.UTF-8 /usr/bin/python3 -E -s -B -m unittest -v test_selected_handoff 실행. 종료 코드 0, 통과 20, 실패·오류 0.
정상 선택, 동일 바이트의 다른 ID와 지정 순서, 실패 전체 중단과 빈 stdout, 미등록·중복·경로 이탈·링크·누락·변조·색인 불일치 거부, 본문 및 임의 필드 미노출, 기본 인계·검색 동등성은 합성 범위에서 PASS.

## 실제 구성의 격리 복사

원본 MVL-01 SQLite를 OS 파일 읽기로만 복사했다. SQLite 접속과 체크포인트는 격리 사본에만 해당한다. 원본 및 복사 전후 SHA-256 755e7695eb3e4e4073906940999665b21248cb1dc1fbf6847c2b8bc84e310eda. 원본의 WAL·SHM·저널 파일 없음, 헤더 버전 [1, 1]. 격리 복사본 quick_check=ok, rollback journal delete. 기존 docs 5527, manual 3, mvl_sources 8. 기존 행 경로 및 해시는 치환하지 않았다.

범위 보호 러너가 승인된 원본 읽기와 신규 폴더의 SQLite 경로를 강제했다. 첫 러너 실행은 Python 3.9의 bytes 감사 이벤트를 문자열로 잘못 해석해 격리 SQLite를 거부했다. SCOPE_RUNNER_ATTEMPT_01.txt에 보존했다. 러너의 경로 디코딩만 바로잡았으며 R01 후보나 기준 코드에는 변경이 없다.

검색 9/9 PASS. 같은 DB에 대한 기준과 후보의 전체 런타임 JSON을 비교했으며, 기존 증거와 순위·점수·중복 묶음·결과 건수도 일치했다. 양쪽 실행에서 같은 읽기 범위를 적용했으며 범위 밖 원본의 해시 검증은 이 결과에 포함하지 않는다.

기본 initial/final의 실제 고정 행 비교는 NOT_TESTED. 양쪽 코드와 두 단계 모두 종료 코드 1, stdout 0바이트. 첫 고정 참조 ASSET-SEARCH-V15-SERVICE의 운영 원본 경로는 현재 승인에서 금지된다. 읽기 함수에 도달하기 전에 경로를 차단했다.
별도로 복사된 기존 MVL01-FEEDBACK의 등록 경로는 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/FEEDBACK_CANDIDATE.md이고 신규 ROOT의 허용 경로는 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_RETURN_R01_V01/FEEDBACK_CANDIDATE.md다. 이 경로 바인딩도 해결돼야 최종 인계를 재시험할 수 있다.

## 환류 후보

- ID MVL-USER-R01-SELECTED-HANDOFF, 판본 1.0, ISOLATED_CANDIDATE. /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_RETURN_R01_V01/incoming/R01_SELECTED_HANDOFF_FEEDBACK.md
- 등록 REGISTERED, 종료 코드 0. 등록 기대값, 원본 직접 해시, 정확 ID 재검색 실측값과 선택 ID 직접 검증 실측값이 모두 d27779d4c17db58fedcb8e16ab9b52eea637b3e80cd53baddf41206eccda5242로 일치했다. 크기 3012바이트. 재검색과 선택 ID 검증 상태 LOCAL_HASH_MATCH. 색인 본문은 비어 있다.
- 실제 기본 및 선택 인계는 둘 다 종료 코드 1, stdout 0바이트. 실제 인계 문서의 후보 제외·포함 및 인계 해시는 NOT_TESTED. 빈 문서를 성공으로 처리하지 않았다.
- 등록 후 격리 DB SHA-256 f374e82cbfd2c989b80c029d668d542ea6223db20db1245a0df91bdd7e0bc8de. 재검색과 인계 시도 후 바이트 변화 없음. quick_check=ok. docs 5528, manual 3, mvl_sources 9.

## 원본과 남은 결정

기존 MVL-01 15개와 R01 13개, 별도 승인 대장·고정 참조 6개의 전후 SHA-256 일치. 운영 검색 서비스 파일은 이번 실행에서 읽지 않았으며 운영 DB·NAS·Firebase·백업·복원·외부 전송에 접근하지 않았다. 공식 대장은 읽기 전용으로 대조했으며 Step 5-C는 BLOCKED다. 전체 저장소 전수 검증은 범위 밖이다.

최소 후속 조건은 첫 고정 참조에 대한 정확한 한 파일의 읽기 전용 해시 검증 승인 또는 승인된 새 출처 계약, 그리고 MVL01-FEEDBACK을 격리 ROOT에 정합적으로 재현하는 방법의 승인이다. 기존 행을 건너뛰거나 운영 DB 접근을 추가할 필요는 없다.
