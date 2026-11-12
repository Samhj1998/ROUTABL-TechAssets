# Claude Code 버전과 경로

| 항목 | 직접 확인 결과 |
|---|---|
| /opt/homebrew/bin/claude --version | 종료 코드 0, 2.1.309 (Claude Code) |
| command -v claude | /opt/homebrew/bin/claude |
| brew list --cask --versions claude-code | claude-code 2.1.309 |
| brew list --cask --versions claude-code@latest | 종료 코드 1, 설치 기록 없음 |
| 심볼릭 링크의 실제 대상 | /opt/homebrew/Caskroom/claude-code/2.1.309/claude |
| 파일 종류·크기 | Mach-O 64-bit executable arm64, 275923296 B |
| 설치 바이너리 SHA-256 | 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c |
| Homebrew 설치 영수증 | /opt/homebrew/Caskroom/claude-code/.metadata/INSTALL_RECEIPT.json |
| 영수증의 source tap·version | homebrew/cask · 2.1.309 |

Homebrew 다운로드 캐시의 Cask/claude-code--2.1.309를 통해 읽은 파일의 크기와 SHA-256도 설치 바이너리와 일치했다. 위 결과와 공식 cask 이름 규칙으로 stable 설치 PASS. CLI 실행은 비대화형 --version에 한정했다.
