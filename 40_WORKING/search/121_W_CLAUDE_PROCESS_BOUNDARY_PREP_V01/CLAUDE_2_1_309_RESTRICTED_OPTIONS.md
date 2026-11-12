# Claude Code 2.1.309 제한 옵션 검증

| 옵션 | 로컬 확인 | 효과와 미검증 범위 |
|---|---|---|
| --restricted | 도움말 | 작업 경로 내 파일 도구, 사용자·프로젝트·local settings 제외, 관리 정책 및 명시 settings 유지 |
| --safe-mode | 도움말 | 사용자 커스텀 설정, hooks/plugins/skills/MCP 등의 로딩 비활성화. 관리 정책 hooks 등 예외 |
| --strict-mcp-config / --mcp-config | 도움말 | 명시 빈 MCP 후보와 결합. 관리 전용 및 앱 등록 예외와 실효 목록 별도 검증 |
| --tools / --disallowedTools | 도움말 | 내장 도구 명시 허용과 금지. 시험은 Read/Edit/Write만 후보 |
| --permission-mode / --settings | 도움말 | dontAsk 후보와 정확한 경로 정책. 자동 승인/우회 모드 사용 금지. 관리 설정의 우선순위 확인 |
| --no-chrome / --disable-slash-commands | 도움말 | 브라우저와 커스텀 명령 추가 제한 후보 |
| --max-turns | 도움말 본문 미표시, 파서 인식 | 4 값과 --help는 종료 0, bogus는 전용 숫자 검증 오류 종료 1. 공식 문서는 --print 전용 agentic turn 제한 |
| --max-budget-usd | 도움말·파서 | 0은 양수 검증 오류. 추정 비용 제한이며 Pro 추가 과금 방지나 정확한 HTTP 요청 수 제한에 사용하지 않음 |
| --print / --output-format / --no-session-persistence | 도움말 | 제한 횟수와 축약 증거를 위한 후보. stream-json 추가 입력 큐 금지 |

가짜 옵션과 --help도 0을 반환했으므로 유효값과 --help의 성공만으로 max-turns 지원을 판단하지 않았다. 잘못된 값에 대한 해당 옵션 전용 파서 오류와 공식 문서를 함께 사용했다. 설치 버전에서 실제 도구 정책·횟수 집행·MCP 비노출의 효과는 NOT_TESTED다. --max-turns를 재시도·인증 갱신·HTTP 건수의 강제 상한으로 간주하지 않는다.

관리 설정 표준 파일 후보와 프로젝트 .mcp.json 부재를 재확인했다. ~/.claude.json은 존재만 확인. 서버 관리 정책, 사용자 MCP 내부 및 Keychain은 미검증이다. --bare는 Pro OAuth에 부적합해 후보에서 제외한다.

[CLI 옵션](https://code.claude.com/docs/en/cli-reference) · [관리 MCP 예외](https://code.claude.com/docs/en/managed-mcp)
