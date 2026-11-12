# 121 Chat / 121-W 1단계 종료 검토 및 Claude Code 설치 범위 결정

당신은 Digitopia 121 Chat의 설계·승인 검토 담당이다. 121-W는 MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403)에서 검색 v1.5 기준선을 실측하고 Claude Code 도입을 사전 점검했다. 결과물은 /Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_BASELINE_V01/ 아래에 있다. 121_W_STAGE1_REPORT.md, BASELINE_BENCHMARK.csv, BASELINE_ACCURACY_REPORT.md, COMMON_TEST_SPEC.md, CLAUDE_MINIMUM_ASSET_MANIFEST.md, CLAUDE_INSTALL_APPROVAL_REQUEST.md와 SHA256SUMS를 확인하라.

운영 검색 ASSET-SEARCH-01 v1.5. 원본 /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_5_service.py, SHA-256 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d. 같은 디렉터리 assets_v1_5.sqlite SHA-256 c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4. 120-2 고정 참조는 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/의 FIRST_IGNITION_CLOSEOUT_REPORT.md (2b893b170bd2a2a4b13f45bf82b1a929d7481e9f5d657a7ebfecb17e1525dd36), SHA256SUMS (2d0f11da7a99302c32cced5f35e753e885b30db1cb75bd1e9a57fb27d92434b8). 둘 다 해시 일치. 기존 PASS는 유효하다.

운영 DB query() 9질의×30회에서 평균 126.89ms, p50 117.66ms, p95 207.52ms, 최대 277.12ms. SQLite 115.70ms 평균, Python 잔여 10.60ms 평균. R08 다건 Python 59.26ms 평균. LIKE가 docs를 스캔하고 FTS5 trigram은 현재 경로에서 사용되지 않는다. 동일 현행 v1.5 함수로 운영 DB와 보존 DB의 기존 9질의를 비교하여 9/9 전체 반환 일치. 운영 HTTP·제어된 cold cache·파일 I/O 분리·운영 refresh는 NOT_TESTED.

1,230행 합성자료로 개발 30/보류 20의 50질의를 시험했다. Recall/MRR/nDCG@10 각 0.80, Precision@10 0.16(상한 0.20), 중복/최신판 표식 각 40/50. 초성은 0/10 FAIL. 합성 메모리 SQLite 색인 전체 143.90ms, 변경 한 행 0.437ms 평균(각 10회). 실운영 관련도와 최신판 일반화는 별도 시험이다.

장치 macOS 27.2 arm64, Homebrew 7.0.11 /opt/homebrew/bin/brew. Claude CLI 흔적 미발견, Node와 npm은 존재하나 stable 설치의 필수 조건은 아니다. 표준 Claude Desktop 설정에서 로컬 MCP 항목 0. 원격 점검 프로세스에 ANTHROPIC_API_KEY 등 설정 미발견. 실제 터미널, 유효 MCP/권한, Pro OAuth, 추가 크레딧 상태는 미검증. 사용자 보고 기준 개인 Pro 월 $20 가입. 공식 stable cask는 claude-code. 설치 후보는 HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ANALYTICS=1 /opt/homebrew/bin/brew install --cask claude-code.

이번에 판단할 항목은 ① 위 Mac 한 대의 stable cask 설치와 버전 확인 승인 여부 ② 사용자 직접 OAuth와 Pro/추가 사용 상태 확인을 함께 진행할지다. 격리 생성과 권한·MCP 시험, 자료 외부 전송, B/C 구현은 별도 범위로 분리하라. 운영 검색, DB, 공식 대장, NAS, Firebase, 자동 결제에 대한 기존 경계를 유지하라.

공통 자료는 매니페스트의 4개 후보만 검토하고, SHA-256 단위로 승인하라. 정확한 운영 회귀 입력 및 보류 자료는 평가자에게만 제공한다. 121-W는 기준선·보류 자료를 알고 있으므로 독립 B안은 새 Work 세션에서, C안은 Claude 전용 환경에서 동일 공개 패킷만 받고 작성한다. 양쪽 최초 분석의 SHA를 동결한 후 비교한다. 결정 이후 실제 작업을 요청할 때 해당 단계만 허용하는 완결된 후속 Work 프롬프트를 작성하라. 환류 후보 명칭은 121-W A 기준선 및 공통 평가 규격 v0.1이다.
