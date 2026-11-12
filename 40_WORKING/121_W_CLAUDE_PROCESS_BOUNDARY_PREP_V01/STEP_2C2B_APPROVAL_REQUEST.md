# 121 Chat 검토용 Step 2-C2-B 승인안

A. 무호출 준비 승인. 전용 prefix의 @anthropic-ai/sandbox-runtime@0.0.81 설치와 해당 영역의 lock/캐시/설정 생성만 별도 결정한다. 설치본 해시를 확인하고 합성 canary로 같은 실제 런타임의 파일·하위 프로세스·네트워크 실패 및 정책 오류 중단을 먼저 검증한다. 기존 홈·저장소·마운트·인증 상태 차단과 IPC/네트워크 정책의 예외를 검토한다. 실제 Claude 전체 프로세스의 로컬 시작 검증이 필요하다면 시작 명령과 무호출 보장을 별도 승인안에 명시한다. OAuth 유지가 광범위 접근에 의존하면 별도 표준 사용자와 사용자 직접 재인증을 별도 승인 대상으로 올린다.

B. 최초 모델 시험 승인. A의 필수 경계 통과와 사용자 별도 승인 뒤 합성 자료만 전송한다. 한 세션, 해시로 고정한 최초 프롬프트 1건, --max-turns 4, Read/Edit/Write만 허용. 실행 옵션 후보는 --restricted, --safe-mode, --no-chrome, --disable-slash-commands, --strict-mcp-config와 명시 빈 MCP 파일, --permission-mode dontAsk, 명시 경로 settings, --print와 구조화 출력, --no-session-persistence다. 이 조합은 실제 환경에서 검증이 필요하다. 고정된 환경과 파일 경로, 도구 목록 및 Pro 인증을 검증하고 시작한다.

모델 왕복 4 이내의 엄격한 HTTP 수준 보장이 필요하면 agentic turn 옵션으로 대체하지 말고, 요청 종류·재시도·인증 갱신을 분리 계수할 수 있는 강제 통제를 먼저 승인·검증한다. 승인 외 호스트, MCP·Bash·외부 프로그램, 새로운 인증/과금 경로, 권한 확대, 예상 밖 쓰기, 실제 자산 노출 또는 테스트 불완전으로 재시도 요구가 발생하면 중단한다. 자동 충전, Console, 신규 OAuth 여부는 확인된 범위를 넘어 PASS 처리하지 않는다.
