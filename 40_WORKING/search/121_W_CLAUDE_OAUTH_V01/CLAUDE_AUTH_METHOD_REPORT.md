# Claude 인증 경로 검증

직접 확인한 로컬 CLI 도움말에서 `auth login`의 기본 경로는 Claude 구독이며 `--console`은 별도 Console API 청구 경로다. `auth status --text` 옵션도 설치본에서 확인했다. 도움말 검증 PASS.

실제 사용자 터미널 출력에서 Claude Pro account 인증 경로와 지정 계정 일치 PASS. 사용자가 브라우저 OAuth 항목도 확인했다고 회신했다. 신규 실행과 기존 로그인 재사용은 구분되지 않았다. 원격 프로세스와 사용자가 실제로 점검한 Mac Studio 터미널에서 각각 40개 인증·게이트웨이 변수 모두 ABSENT. 현재 CLI는 대상 Pro 계정 경로로 표시됐다. 사용자 확인 이후 원시 출력은 보고하지 않고 로그인 상태, 구독 경로, 대상 계정 일치 여부만 기록한다. 모델 질의는 인증 검증의 범위 밖이다.

[Claude 구독을 Claude Code에 연결](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-max-or-ultra-plan)
