# MVL-01 First Ignition 최종 종료 검증

실측 시각 2026-11-08T08:35:12+09:00. MacStudioui-MacStudio.local, 장치 ID c377300b-a710-43a6-8169-f17e87175403.
격리 폴더 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01

| 판정 | 결과 | 근거 |
| --- | --- | --- |
| R01 독립 활용 검증 | PASS | 독립 개선과 기존 패치 재현, 합성 20/20의 증거 해시를 재확인. 본 세션에서 R01 코드 바이트를 대조. |
| 환류 완주 | PASS | 등록, ID 재검색, 직접 SHA-256, 기본 제외와 선택 포함을 실제 격리 DB로 검증. |
| First Ignition | PASS | 기존 자산 활용, 독립 AI 개발, 독립 재검증, 환류 및 재인계 증거가 연결됨. |
| 최소 완성판 | PASS | 재실행 가능한 격리 경로와 안내서, 필수 기능 검증, 기본 데이터 안전성 확보. |

## 새로 실행한 검증

- 운영 검색 v1.5 고정 원본 한 건은 정규 파일이고 심볼릭 링크가 아니다. SHA-256 기대값 및 실측 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d. 나머지 여섯 고정 참조도 기대값과 일치했다. 운영 서비스 파일은 읽기 전용 해시 계산으로 확인했다.
- 최초 MVL-01 격리 DB는 WAL·SHM·저널 부수 파일 없이 읽기 전용 바이트 사본으로 확보했다. 복사 전후 원본 SHA-256 755e7695eb3e4e4073906940999665b21248cb1dc1fbf6847c2b8bc84e310eda. 원본을 SQLite로 열거나 체크포인트를 실행하지 않았다.
- MVL01-FEEDBACK 판본 0.1, 2,187바이트, 기대 및 실측 SHA-256 04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3. 격리 DB의 MVL/MVL01-FEEDBACK 한 행에서 source_path만 변경했다. docs·manual 및 나머지 mvl_sources 행 해시는 정합화 전후 동일하다. SQLite integrity_check=ok.
  - 이전 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/FEEDBACK_CANDIDATE.md
  - 이후 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/FEEDBACK_CANDIDATE.md
- 기준/R01 코드의 기본 initial 7행 및 final 8행은 각각 종료 0, Markdown 바이트와 구조화 메타데이터 일치. 검색 회귀 이번 실측 9/9 PASS. 이전 9/9는 별개 기록이며 범위 밖 원본의 직접 해시는 수행하지 않았다.
- 후보 MVL-USER-R01-SELECTED-HANDOFF, 판본 1.0, ISOLATED_CANDIDATE, 3,012바이트, REGISTERED. 파일 직접 계산, 등록 기대값, 재검색 및 선택 인계의 기대/실측 SHA-256은 d27779d4c17db58fedcb8e16ab9b52eea637b3e80cd53baddf41206eccda5242. 상태 LOCAL_HASH_MATCH.
- 기본/선택 final 모두 종료 0. 기본 8행에는 후보 없음, 선택 9행에는 후보가 정확히 한 건 추가됨. 고정 8행의 값과 순서를 보존했고 후보 본문 및 임의 비인가 필드는 출력되지 않았다.
  - 기본 final SHA-256 ebc1f131760e253ea6e0ca37f753461e5de5c8149e0e2612a93cd0297134f02d
  - 선택 final SHA-256 da3aa1e9bc9b166a066797b11c39cedc6957393f06fca16cd01c03e1fcf3dae5
- 미등록·중복 요청 두 건 모두 종료 1과 빈 stdout으로 거부했다. 등록 후 인계 및 부정 시험에서 격리 DB SHA-256 dc72ddd7561b5a882dfb49f2865098bde435dc1c04352c6cd3dbbd699368d0bf 유지.
- R01 패치 재현 SHA-256 e8f3b458475e5d783e98bf0f2b1ebe6ccc2235a4355df70b44aea59ef1ab8fdd. 이전 재현 및 20/20 합성 시험은 이전 세션 증거이며 이번에 합성 시험을 다시 실행하지 않았다. 기존 러너의 허용 ROOT 명칭만 새 폴더에 맞췄으며 실제 인계와 검색·부정 시험으로 검증했다. 첫 준비 스크립트의 subprocess import 누락은 SETUP_ATTEMPT_01.txt에 남겼다. R01 코드와 DB에는 해당 오류로 인한 변경이 없다.

## 보호 범위 및 남은 과제

기존 MVL-01 26개, 독립 R01 13개, 최초 반환 27개, 승인 고정 원본 7개의 전후 바이트 SHA-256 일치. 저장소 전체 바이트 감사와 실제 백업은 NOT_TESTED. 운영 서비스 실행·변경, 운영 DB, Firebase·NAS, 백업·복원, Step 5-C 게시, 외부 전송은 실행 범위에서 제외했다.

P0/P1은 이번 완료 범위에서 미해결 항목 없음. P2는 장기 반복 운용, 증분 색인, 속도·정확도 계측 및 최적화, UI 개선이다. v043 백업 운영 전환은 별도 범위다. 재실행 안내는 RUN_GUIDE.md. 모든 결과 파일의 해시는 SHA256SUMS에 있다. 목록 파일 자체의 SHA-256은 최종 보고에 별도 기재한다.
