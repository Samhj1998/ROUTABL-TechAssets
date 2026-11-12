# 121-W Step 2-C1 결과 및 121 Chat 인계

2026-11-08 KST. MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403), Homebrew stable Claude Code 2.1.309, /opt/homebrew/bin/claude, 바이너리 SHA-256 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c.

| 판정 대상 | 상태 |
|---|---|
| Step 2-A·2-B 증거 무결성 | PASS · 5/5 및 6/6 |
| 신규 폴더 구조·실경로·모드 및 빈 input | PASS |
| 작업 폴더만으로 같은 UID 접근 차단 | FAIL · 형제 합성 경로 읽기·쓰기 가능 |
| 독립 로컬 Seatbelt의 합성 파일 시험 | PASS · 기대 12/12 |
| Claude 설정·MCP 정적 파일 위치·도움말 점검 | PASS · 민감한 사용자 상태 파일은 메타데이터만 |
| Claude 내장 도구·셸의 실효 격리, 실효 MCP·네트워크 | NOT_TESTED |
| 모델 호출 | 0건 |

격리 위치 /Users/yongho/121_CLAUDE_ISOLATED_V01/. 보고 위치 /Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_CLAUDE_ISOLATION_PREP_V01/. 보고서와 합성 시험물의 SHA-256은 SHA256SUMS에서 확인한다. 준비 단계의 승인 범위를 완료했다. 운영용 실효 격리 판정은 보류한다.

## 121 Chat에 붙여넣을 프롬프트

당신은 Digitopia 121 Chat의 설계·승인 담당이다. 121-W Step 2-C1은 장치 MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403)에서 Claude Code 2.1.309의 바이너리 SHA-256 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c와 Step 2-A/2-B 증거 5/5·6/6을 확인했다. Step 2-B 전체는 기존 기준 NOT_TESTED다. 사용자 승인 ②안에 따라 Pro의 Usage credits 꺼짐·잔액 US$0을 현재 Pro 경로 추가 사용량 과금 차단 근거로 사용한다. 자동 충전·별도 Console·신규 OAuth 실행 여부는 NOT_TESTED. 점검 변수 40개는 원격과 이전 실제 사용자 터미널에서 모두 ABSENT다.

신규 /Users/yongho/121_CLAUDE_ISOLATED_V01/의 input은 비어 있고 0500, output/scratch/config/tests는 0700이다. 같은 UID의 일반 실행에서 합성 형제 디렉터리의 절대·상위·링크 경로 읽기 및 쓰기가 허용되어 폴더 단독 격리는 FAIL. 별도 macOS Seatbelt 프로필과 Python으로 합성 시험 12/12 PASS. 프로필은 Claude 운영 경계가 아니며 내장 파일 도구·Bash·MCP·네트워크 실효 시험은 NOT_TESTED다. 사용자 상태 파일은 메타데이터만 봤다. 로컬 CLI 도움말에서 --restricted, --safe-mode, --strict-mcp-config와 도구 목록 제어를 확인했다. 실제 도구·모델 호출은 없었다.

/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_CLAUDE_ISOLATION_PREP_V01/의 STEP_2C2_APPROVAL_REQUEST.md, LOCAL_BOUNDARY_TEST_REPORT.md, CLAUDE_SETTINGS_INVENTORY.md, MCP_STATIC_INVENTORY.md와 SHA256SUMS를 검토하라. ① 전용 macOS 사용자 또는 동등한 전체 프로세스 경계 ② 실제 모델을 호출하지 않는 준비 검증의 승인 범위 ③ 그 검증 PASS 뒤 합성 파일 전용 최초 Claude 도구 시험의 최소 승인 범위와 비용·중단 조건을 결정하라. C2 1차는 제한 모드 내장 파일 도구, Bash는 별도 선택이다. 공통 자료 복사·전송, 운영 자산 접근 및 B/C 독립 개발은 별도 승인으로 유지한다. 실제 실행을 승인할 경우 범위와 중단 조건을 담은 완결된 Work 프롬프트를 작성하라.
