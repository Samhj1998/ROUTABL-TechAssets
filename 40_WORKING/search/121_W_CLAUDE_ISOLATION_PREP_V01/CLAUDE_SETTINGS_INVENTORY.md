# Claude Code 설정 정적 인벤토리

설치본 2.1.309, /opt/homebrew/bin/claude, SHA-256 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c. 실행은 --version, --help, mcp --help에 한정했다.

| 범위 | 현재 Mac에서 확인한 파일 상태 |
|---|---|
| 사용자 | ~/.claude 디렉터리 0700, ~/.claude.json 파일 0600. ~/.claude/settings.json, settings.local.json, CLAUDE.md, rules, hooks, plugins, skills, agents, commands, projects, .credentials.json 점검 경로에서 미발견 |
| 상위·작업 경로 | /, /Users, /Users/yongho, 신규 루트에서 CLAUDE.md, CLAUDE.local.md, .claude의 알려진 프로젝트 설정, .mcp.json 및 .git 미발견. 신규 scratch·output·합성 work의 자동 로딩 후보도 미발견 |
| 관리 | /Library/Application Support/ClaudeCode/managed-settings.json, managed-settings.d, managed-mcp.json 및 조사한 MDM plist 후보 미발견. 서버 제공 및 전체 MDM 정책은 NOT_TESTED |
| 인증·외부 공급자 | 승인 목록 40개 원격 프로세스에서 모두 ABSENT. 점검 위치에 일반 settings 파일이 없었다. 인증 관련 파일 및 Keychain은 열람하지 않았다 |
| Desktop | Claude Desktop 설정 파일 0600 존재, 메타데이터만 확인. 이번 단계의 내부 설정 항목은 NOT_TESTED |

공식 문서상 일반 설정 우선순위는 관리 → 명령줄 --settings → 프로젝트 로컬 → 프로젝트 공유 → 사용자다. 배열 병합과 일부 보안 키의 예외가 있으며 환경 변수는 키별 규칙을 따른다. 홈 설정 파일에 값이 없다거나 모든 승인 규칙·hooks·관리 정책이 비활성이라고 단정하지 않는다.

설치본 도움말에서 --restricted, --safe-mode, --settings, --setting-sources, --tools, --permission-mode, --mcp-config, --strict-mcp-config, --disable-slash-commands, --no-chrome를 확인했다. --restricted 설명은 작업 디렉터리에 파일 도구를 제한하고 사용자·프로젝트·로컬 settings를 무시하되 관리 및 명시 --settings를 남긴다. 명시 허용한 Bash는 별도 검증이 필요하다. --bare는 설치본 도움말상 OAuth 및 Keychain을 읽지 않으므로 Pro 경로 시험 후보에서 제외한다. --no-session-persistence는 설치본 도움말상 --print 전용이다. 실제 옵션 조합 및 설정 키 런타임 적용은 NOT_TESTED.

[설정 범위와 우선순위](https://code.claude.com/docs/en/settings) · [CLI 옵션](https://code.claude.com/docs/en/cli-reference)
