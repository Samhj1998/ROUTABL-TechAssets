# B/C 독립 구현과 접근 경계

B는 별도의 `121-B-W` 세션에서 진행했다. 121-W는 B에 장치, B 전용 경로, 동일 지시문과 입력 해시만 인계했다. B가 요청한 신규 입력 3건의 배치 당시 SHA를 확인해 회신했고, 최초 완료 통보의 7개 SHA와 구현 자체 체크섬의 10개 행을 Mac Studio에서 독립적으로 재검산했다. 121-W는 B 소스나 시험 코드를 작성하거나 고치지 않았다. B 도구 호출 전체의 독립 감사 로그는 이 평가자 세션에 없다.

C는 같은 Mac의 C 구현 디렉터리를 작업 경로로 Claude Code 2.1.309를 실행했다. 승인된 Claude Pro 계정 경로 및 실제 원격 실행의 인증·게이트웨이 변수 40개 미설정을 재검증했다. Usage credits는 앞서 동결한 비활성 화면 증거를 사용했다. 자동 충전과 Console 상태는 기존 NOT_TESTED를 유지한다.

C 세션은 restricted/safe-mode, 빈 MCP, no-chrome, dontAsk, 허용 도구 4종으로 실행했다. 모델 최초 본문은 공통 지시문 사본을 바이트 그대로 사용했다. 셸은 별도 sandbox로 제한하고 Python 합성 시험 명령 한 개만 허용했다. 첫 실행이 시간 제한에 도달한 뒤, 기존 소스·시험 로그를 읽기 전용으로 두고 C의 보고서·체크섬 작성만 별도 유한 실행으로 이어갔다. 그 실행의 셸 허용은 세 보고서 해시 명령 한 개다. 실행 로그의 tool init에서 MCP 0개와 승인된 도구를 확인했다. Claude Code가 작업 루트에 자체 생성한 `.claude/.cc-writes`는 CLI 보조 메타데이터로 확인됐고 산출물은 각 후보의 src/tests/output에서 별도로 동결한다.

양쪽에 평가자용 질의와 운영 데이터, 상대 분석·코드를 제공하지 않았다. C에는 평가자 집계·보고서나 B 중간 결과를 전달하지 않았다. 동일 UID가 운영환경에 가진 기술적 접근 범위에 대한 별도 격리 합격 판정을 내리지 않았다. 121-W에서 실제 운영 9질의, 보류 20질의 후보 채점 및 공식 A/B/C 비교를 수행하지 않았다.

근거 `STAGING_AND_COHORT_EVIDENCE.json`, `C_CLI_POLICY.json`, `C_EXECUTION_EVIDENCE.json`, `C_CLI_POLICY_FINALIZE.json`, `B_FREEZE_ARTIFACTS.json` 및 후보별 결과 매니페스트.
