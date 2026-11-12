# MCP 정적 인벤토리

| 범위 | 정적 점검 |
|---|---|
| 신규 프로젝트 | 루트·scratch·output·합성 work의 .mcp.json 없음 |
| 상위 경로 | /, /Users, /Users/yongho에서 .mcp.json 없음 |
| 사용자 및 프로젝트 local | ~/.claude.json 존재. 인증 정보를 포함할 수 있는 파일이므로 메타데이터만 확인했다. 선언 수와 실제 서버는 NOT_TESTED |
| Desktop | Claude Desktop 설정 파일 존재. 이번 단계 내부 설정은 NOT_TESTED |
| 관리 | 표준 managed-mcp.json 및 managed-settings.json/디렉터리 없음. 서버 관리 및 앱 등록 커넥터 실효 상태 NOT_TESTED |
| 신규 후보 | /Users/yongho/121_CLAUDE_ISOLATED_V01/config/mcp-empty.CANDIDATE.json · mcpServers 0건. 비활성 후보 파일 |

공식 문서상 일반 MCP 이름 중복 우선순위는 local → project → user → 플러그인 → claude.ai 커넥터다. 관리 전용 MCP 정책이 별도로 적용될 수 있고, 앱 등록 또는 관리 제공 서버에는 예외가 있다. 프로젝트 승인 상태 및 상위 우선순위 때문에 파일 부재만으로 자동 활성화 가능성을 배제하지 않는다.

설치본 도움말에서 --strict-mcp-config와 --mcp-config, mcp 하위 명령을 확인했다. 실제 서버 조회·헬스체크 가능성이 있는 명령은 사용하지 않았다. C2에서 --safe-mode 및 빈 명시 MCP 후보를 검토하고, 실효 도구 목록 확인은 세션과 네트워크 승인에 맞춰 수행한다. MCP 실제 연결·실효 목록은 NOT_TESTED.

[MCP 범위와 우선순위](https://code.claude.com/docs/en/mcp) · [관리 MCP 예외](https://code.claude.com/docs/en/managed-mcp)
