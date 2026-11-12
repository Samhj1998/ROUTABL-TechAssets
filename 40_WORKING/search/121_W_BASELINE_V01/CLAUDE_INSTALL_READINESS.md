# Claude Code 설치 준비 점검

- 점검 장치 MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403
- 2026-11-08 KST. macOS 27.2 (26B123), arm64, 36 GiB RAM, 홈 볼륨 여유 134,654,005,248 B.
- Homebrew 7.0.11, /opt/homebrew/bin/brew. 원격 실행 계정에서 /opt/homebrew 쓰기 가능 판정. 실제 설치 권한·다운로드·실행은 별도 확인 대상이다.
- PATH 및 대표 native/Homebrew/npm 경로에서 claude CLI를 발견하지 못했다. Apple Silicon 및 Intel의 점검 대상 cask 경로에서 stable/latest 흔적이 없었다. 따라서 현재 CLI 버전은 NOT_TESTED. 다른 설치 관리자나 별도 환경에 관한 전수 조사는 범위 밖이다.
- Node.js v24.21.0, npm 11.19.0, 각각 /usr/local/bin. stable cask는 사전 빌드된 arm64 바이너리를 직접 설치하며 이 경로의 필수 조건에 Node/npm이 없다.
- ~/.claude 디렉터리와 Claude Desktop 설정 파일 존재. Desktop 설정의 로컬 mcpServers 항목 수 0. 조사한 표준 CLI 사용자/프로젝트/관리 설정 파일 및 CLI 세션 디렉터리는 발견하지 못했다. 원격 커넥터·키체인·관리 프로필·미래 세션의 유효 설정은 별도로 검증해야 한다.
- ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN, ANTHROPIC_BASE_URL, CLAUDE_CODE_USE_BEDROCK/VERTEX/FOUNDRY, CLAUDE_CONFIG_DIR, CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE는 점검한 원격 프로세스 환경에서 미발견. 실제 사용자 터미널에서 다시 확인한다.

| 항목 | 판정 |
|---|---|
| 장치 식별 및 기본 요구사항 | PASS |
| Homebrew stable 공식 설치 경로 | PASS |
| 점검 경로에서 충돌 확인 | PASS |
| 실제 다운로드·설치·버전 확인 | NOT_TESTED |
| Pro 로그인·계정 과금 설정 | NOT_TESTED |
| 새 세션의 유효 권한·MCP 및 격리 시험 | NOT_TESTED |

후속 승인 후 설치 후보는 `HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ANALYTICS=1 /opt/homebrew/bin/brew install --cask claude-code`이다. 이어서 `/opt/homebrew/bin/claude --version`, `command -v claude`, 설치 cask를 확인한다. 해당 패키지 업데이트는 수동으로 관리하며 자동 업데이트 opt-in을 사용하지 않는다. 현재 단계의 Homebrew 호출은 버전 확인에 한정했다.

[Anthropic 고급 설치 문서](https://code.claude.com/docs/en/setup) · [Homebrew stable cask](https://formulae.brew.sh/cask/claude-code) · [Homebrew cask 구현](https://github.com/Homebrew/homebrew-cask/blob/main/Casks/c/claude-code.rb)
