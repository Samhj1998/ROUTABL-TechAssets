# Claude Code 보안·과금 검토

## 인증과 비용

- 사용자 제공 정보는 2026-11-08 개인 Claude Pro 월 $20 결제. 실제 계정 권한, 결제 화면, 추가 사용 상태는 미검증이다.
- 사용자 본인이 브라우저에서 Claude Pro 개인 계정으로 OAuth 인증한다. CLI에서 지원하는 상태 표시 및 `/status`로 구독 인증 경로를 확인한다. 보고에는 로그인 상태와 구독 유형만 남긴다.
- Anthropic 문서상 ANTHROPIC_API_KEY가 설정되면 API 키 과금으로 연결될 수 있다. 실제 실행 터미널에서 키·토큰·커스텀 endpoint·외부 제공자 설정 및 apiKeyHelper 활성 여부를 확인한다. 값은 표시하지 않는다. 발견하면 해당 세션을 시작하기 전에 원인을 해결한다.
- Claude와 Claude Code는 Pro 포함 한도를 공유한다. Claude Settings > Usage에서 Usage credits 및 자동 충전이 비활성인지 사용자가 확인한다. 한도에 도달하면 다음 초기화까지 중단한다.
- 개인정보 설정에서 모델 개선용 데이터 사용을 비활성화할 것을 권장한다. 이 설정은 승인 자료의 모델 처리 전송과 별개다. 공식 소비자 정책 기준 비동의 시 서버 보관 30일, 동의 시 5년이며 일반 로컬 CLI 대화는 기본적으로 ~/.claude/projects/ 아래 평문으로 보관된다. 별도 CLAUDE_CONFIG_DIR 사용 시 그 위치로 분리된다. 코드·문서가 프롬프트, 도구 결과, 진단 및 피드백에 들어가지 않도록 제공 범위를 제한한다.

## 최초 세션 격리안

1. 제안 작업 위치 /Users/yongho/121_CLAUDE_ISOLATED_V01/을 후속 승인 후 생성한다. 읽기 전용 입력과 쓰기 전용 범위를 분리한다. 복사본의 실제 경로와 SHA를 검증하고 심볼릭 링크와 승인되지 않은 외부 경로를 검사한다.
2. 전용 로컬 사용자 또는 동등한 OS 접근 차단을 우선 검토한다. 계정 추가나 권한 변경에는 별도 승인이 필요하다. 현재 계정으로 진행하는 경우에도 원본 저장소, 운영 검색 폴더, 사용자 자격증명, NAS/공유 볼륨에 대한 접근 차단을 실제 시험한 뒤 자료를 제공한다.
3. 사용자·상위 경로의 CLAUDE.md, .claude 설정, hooks, plugins, skills, MCP, 관리 설정, 환경 변수, 리포 연결을 점검한다. 빈 승인 MCP 구성과 `--strict-mcp-config`를 검토하고, 관리 설정에 따른 예외 및 실효 목록을 확인한다. 추가 디렉터리 연결은 사용하지 않는다.
4. 첫 독립 분석은 Plan 모드와 제한된 도구 목록으로 진행하고 결과는 터미널 출력 또는 사용자 수동 저장으로 고정한다. 여기서 Manual은 후속 구현에서 승인된 작업만 검토하는 운영 방식이며, 공식 CLI 모드는 `default`다. 기본 모드에서 일부 읽기 명령은 개별 승인 없이 실행될 수 있다. auto/bypass/항상 허용은 사용하지 않는다.
5. Bash가 필요해지면 sandbox를 켜고 failIfUnavailable=true 및 allowUnsandboxedCommands=false를 검토한다. 기본 읽기 범위가 넓으므로 읽기·쓰기 제한과 허용 네트워크를 구성한다. Bash sandbox와 CLI Read/Edit 권한은 따로 검증한다. 동작 시험은 무해한 경계 파일을 대상으로 CLI 읽기, 셸 읽기·쓰기, symlink, 상위 경로, MCP, 네트워크를 확인한다. 테스트 실행 결과가 있기 전에는 격리 PASS로 판정하지 않는다.
6. 명령행·로컬 로그에 비밀이 들어가지 않도록 하고 사용자 확인 없이 /feedback에 세션을 보내거나 클라우드 세션 및 연결 기능을 사용하지 않는다.

판정은 문서 대조 PASS, 원격 프로세스 환경 변수 점검 PASS, 계정 상태·실제 과금 경로·파일 경계·MCP 유효 상태 NOT_TESTED.

[Pro 구독 인증과 API 키](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-max-or-ultra-plan) · [사용량 크레딧](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans) · [데이터 사용](https://code.claude.com/docs/en/data-usage) · [권한](https://code.claude.com/docs/en/permissions) · [샌드박스](https://code.claude.com/docs/en/sandboxing) · [CLI](https://code.claude.com/docs/en/cli-reference)
