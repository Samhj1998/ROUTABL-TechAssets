# 121-W Step 2-A 설치 결과

장치 MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403. macOS 27.2, arm64, Homebrew 7.0.11. 2026-11-08 KST.

| 검증 항목 | 판정 | 결과 |
|---|---|---|
| 설치 전 환경·충돌 점검 | PASS | PATH 및 대표 경로에 기존 CLI 미발견, stable/latest cask 없음, 설치 디렉터리 쓰기 가능 |
| stable cask 설치 | PASS | 승인된 명령 1회 실행, 종료 코드 0 |
| 설치 버전·경로 검증 | PASS | 2.1.309 (Claude Code), /opt/homebrew/bin/claude |
| 기존 패키지 목록 비교 | PASS | stable cask 1건 추가, 기존 formula·cask 버전 목록 일치 |
| 원본 SHA-256 보존 검증 | PASS | 지정 네 파일 4/4 일치 |
| 사용자 OAuth·구독·과금 설정 | NOT_TESTED | 별도 승인 범위 |
| Claude 최초 대화·파일 격리·MCP·자료 제공 | NOT_TESTED | 별도 승인 범위 |

실행 명령
```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ANALYTICS=1 /opt/homebrew/bin/brew install --cask claude-code
```

2026-11-08 10:22:03 KST 시작, 10:22:24 KST 완료. 승인된 설치 호출은 한 번이다. Homebrew 출력의 설치 증거

```text
Fetching downloads for: claude-code
Cask claude-code (2.1.309)
Installing Cask claude-code
Linking Binary 'claude' to '/opt/homebrew/bin/claude'
claude-code was successfully installed!
install_exit 0
```

공개 Homebrew 조회 시 표시한 2.1.311과 실제 Mac의 설치 결과 2.1.309를 구분한다. 설치 결과는 실행 파일과 로컬 Homebrew 기록에서 확인했다. 공개 표시와 설치 시 해석된 버전 차이의 원인은 별도로 판정하지 않았다.

[Homebrew 공식 cask](https://formulae.brew.sh/cask/claude-code) · [Anthropic 공식 채널 안내](https://code.claude.com/docs/en/setup)
