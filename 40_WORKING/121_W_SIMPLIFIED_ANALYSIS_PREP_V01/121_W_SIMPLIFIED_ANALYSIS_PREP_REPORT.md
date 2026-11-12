# 121-W 간소화된 독립 분석 착수 준비

2026-11-08 KST, MacStudioui-MacStudio.local, 장치 c377300b-a710-43a6-8169-f17e87175403. 사용자는 기술자산을 AI 분석에 활용할 수 있는 일반 작업 자료로 분류했다. 보호 대상은 인증 비밀, 실제 고객 개인정보 및 운영 원본의 변경 권한이다. 전체 프로세스 격리 연구는 보류한다. C1의 동일 UID 폴더 단독 격리 FAIL 및 Seatbelt 합성 PASS는 기존 기록으로 유지한다. Step 2-B 전체 NOT_TESTED, Pro 인증과 Usage credits 비활성 PASS도 기존 판정대로 유지한다.

## 공통 입력 확정

원본 /Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_BASELINE_V01/. 기준 매니페스트 CLAUDE_MINIMUM_ASSET_MANIFEST.md의 SHA-256 b65db09df1012b5ef05c520157af2ff954fd71258256475a0b6be5b5089307d1 일치. 아래 파일의 판본은 모두 v0.1이며 해시와 크기를 직접 확인했다.

| 파일 | 바이트 | SHA-256 | 비밀·개인정보 점검 |
|---|---:|---|---|
| COMMON_ANALYSIS_PACKET_V01.md | 1944 | d88a5a12e4a814105991fce95391079e7cdd22cddee0296d5ad33d3812c69bba | 특이 항목 미발견 |
| SYNTHETIC_CORPUS_V01.json | 1097578 | 840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b | 특이 항목 미발견 |
| SYNTHETIC_DEV_V01.json | 14829 | db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1 | 특이 항목 미발견 |
| COMMON_TEST_SPEC.md | 3471 | 552bb8111f703048e657a26922954f2739156362efa37f54f5f7e5cf1e254f6d | 특이 항목 미발견 |

네 파일 전체 바이트에서 개인키, 서비스 토큰, JWT, Bearer, 비밀번호·비밀값 할당, URL 내 인증, 이메일, 한국 전화·주민번호·도로명 상세 주소 및 고객 필드 패턴을 조사했다. 검출 0건. 마크다운은 기술 규칙 및 평가 절차이며 JSON의 코퍼스 1,230행은 모두 00_SYNTHETIC 경로에 있고, 개발 질의 30개는 모두 dev split이다. 공통 자료 4건을 최초 승인 대상 패킷으로 확정한다. 이 판정은 해당 해시로 고정된 파일에 한정된다.

## 작업 위치 및 독립성

| 역할 | 입력 | 출력 |
|---|---|---|
| B · 새 ChatGPT Work 분석 세션 | /Users/yongho/121_CHATGPT_B_V01/input/ | /Users/yongho/121_CHATGPT_B_V01/output/ANALYSIS_B.md |
| C · Claude Code 분석 세션 | /Users/yongho/121_CLAUDE_ISOLATED_V01/input/ | /Users/yongho/121_CLAUDE_ISOLATED_V01/output/ANALYSIS_C.md |
| 비교 평가자 · 기존 121-W | 봉인된 B/C 결과와 별도 평가 자료 | 두 결과 봉인 후 비교 |

C 폴더는 실제 경로 일치, input 0500 및 비어 있음, output/scratch 0700 및 비어 있음. config의 명시 빈 MCP 후보를 확인했다. 프로젝트 자동 설정 파일과 조사한 관리 설정 파일 위치에는 파일이 없었다. 홈 상태 파일은 존재만 확인했다. Claude 바이너리 SHA-256 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c 일치. 원격 환경 변수 40개는 모두 ABSENT. B 경로는 신규 후보이며 아직 존재하지 않는다.

승인 후 각 input에 정확한 네 파일만 로컬 배치하고 원본·사본 SHA-256을 다시 검증한다. C의 input 모드를 배치 후 0500으로 되돌리고 입력 파일은 0400으로 둔다. 두 세션에 동일한 본문 프롬프트를 제공하며 상대의 결과·보류 20건·운영 DB 및 실제 질의는 평가자만 취급한다. 모델 출력은 Markdown으로 수집한다. 같은 포맷을 사용하고 B/C 결과를 각각 SHA-256과 함께 동결한 뒤에만 개봉한다.

## 첫 C 실행과 비용·중단

별도 인사 프롬프트를 줄이기 위해 첫 독립 분석 프롬프트 자체에서 공통 자료 읽기 확인을 한다. C는 패킷 input을 cwd로, 파일 읽기만 허용한다. 설치본에서 확인한 --restricted, --safe-mode, --no-chrome, --strict-mcp-config와 기존 빈 --mcp-config를 후보로 적용한다. --tools Read와 dontAsk, 정확한 네 경로의 읽기 허용만 명시하고 추가 디렉터리는 연결하지 않는다. Work가 구조화 출력을 받아 승인된 output에 보고서를 저장한다. Bash나 코드 편집 도구가 없어도 이번 분석을 수행할 수 있다.

시작 직전 현 실행 환경에서 변수 존재 여부 및 기존 Claude Pro 인증을 확인한다. Usage credits 비활성의 사용자 확인 근거를 점검한다. 개인 Pro만 사용한다. 초기 프롬프트 1건, --print의 --max-turns 4 후보, 추가 메시지·자동 재시도 없음. max-turns는 agentic turn 제한이며 HTTP 요청 수 상한은 아니다. 인증 유형 변경, 키·토큰·고객 개인정보 검출, 해시 불일치, 예상 밖 도구나 경로, 사용량 한도 또는 크레딧·과금 전환 요청 시 중단한다. 입력을 하나라도 읽지 못하면 미완료를 표시한다. 운영 원본의 변경, 코드 구현, 보류시험 접근은 별도 단계다.

이번 준비 단계의 모델 호출·Claude 대상 자료 전송·입력 배치는 0건이다. 기존 합성 시험을 재사용하며 재실행을 준비 조건으로 요구하지 않는다.

## 다음 Work 실행 승인에 붙일 문구

MacStudioui-MacStudio.local에서 위 네 파일의 정확한 해시를 재확인하고 B/C의 분리 input에 로컬 배치하는 작업, 이 패킷 네 파일의 Claude Pro 모델 제공, 새 B 세션 및 C의 독립 분석 첫 프롬프트 각 1건을 승인한다. C는 위 읽기 전용·비용·중단 조건으로 진행하고 양측 Markdown과 SHA-256을 따로 동결하라. `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_SIMPLIFIED_ANALYSIS_PREP_V01/121_BC_SHARED_ANALYSIS_PROMPT.md`의 본문을 양측에 동일하게 적용하라. 운영 자산·보류 세트·상대 결과는 제공 범위에서 제외하고, 코드 구현 또는 결과 비교 전 다음 지시를 기다려라.

[Claude CLI 제한 옵션](https://code.claude.com/docs/en/cli-reference) · [Usage credits](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans)
