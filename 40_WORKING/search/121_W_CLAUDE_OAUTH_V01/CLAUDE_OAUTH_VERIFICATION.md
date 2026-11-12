# Claude Code OAuth 검증 기록

검증 장치는 MacStudioui-MacStudio.local, 장치 ID c377300b-a710-43a6-8169-f17e87175403. 설치본 2.1.309와 바이너리 SHA-256 5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c를 원격 Mac에서 재확인했다. 검사일 2026-11-08 KST.

| 항목 | 판정 | 근거 |
|---|---|---|
| CLI 설치본과 인증 명령 지원 | PASS | 버전·해시 확인. `auth login --help`, `auth status --help` 종료 코드 0 |
| 실제 사용자 터미널 환경 | PASS | 사용자 제공 출력에서 40개 모두 ABSENT |
| 브라우저 OAuth 확인 | 사용자 확인 | 사용자가 이번 OAuth 항목을 확인했다고 회신. 신규 실행인지 기존 인증 재사용인지 회신에서 구분되지 않음 |
| CLI 인증 상태 | PASS | 사용자가 실제 Mac Studio 터미널에서 확인한 표시값은 Claude Pro account |
| 대상 계정 일치 | PASS | CLI 이메일과 지정 계정 일치, 사용자 제공 출력 |

인증은 Mac Studio 사용자 터미널에서 사전 점검을 통과한 뒤 사용자 직접 실행이 필요하다. 기존 정상 구독 로그인이 있으면 보존한다. 실제 터미널 결과는 2026-11-08 KST 대화에서 수신했다.
