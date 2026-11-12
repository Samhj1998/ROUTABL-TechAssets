# 로컬 합성 파일 시험

시험 주체는 macOS 사용자 UID 501의 Python 자식 프로세스다. 실제 Claude CLI 도구 호출이 없는 대조 시험으로, 기록은 /Users/yongho/121_CLAUDE_ISOLATED_V01/tests/local-boundary-results.json에 있다.

| 동작 | 일반 동일 UID | 합성 Seatbelt 프로필 |
|---|---|---|
| 작업 파일 읽기 | 허용 | 허용 |
| 읽기 전용 파일 읽기 | 허용 | 허용 |
| 읽기 전용 위치 생성·수정 | 2건 차단 | 2건 차단 |
| output 파일 생성·읽기·수정·삭제 | 허용 | 허용 |
| scratch 파일 생성·읽기·수정·삭제 | 허용 | 허용 |
| 형제 합성 파일 절대경로·../·링크 읽기 | 3건 허용 | 3건 차단 |
| 형제 합성 파일 생성·수정·삭제 | 3건 허용 | 3건 차단 |

두 실행 모두 종료 코드 0. 케이스별 OS 거부는 EACCES 또는 EPERM으로 확인했다. 일반 동일 UID의 여섯 허용은 작업 경로만으로 격리할 수 없음을 보여준다. Seatbelt 샘플의 기대 결과는 12/12 일치했다. 심볼릭 링크는 시험 후 제거했고 기존 자산 파일은 시험 대상에 넣지 않았다.

프로필에는 네트워크 차단 규칙이 있지만 연결 실험은 수행하지 않았다. 공식 문서상 Claude Bash 샌드박스와 내장 Read/Edit/Write의 정책은 별개이고, hooks·MCP·인증 도우미 등도 별도 경계를 가진다. 현재 시험 결과를 Claude의 도구 실행·네트워크·원본 접근 실효 PASS로 전용하지 않는다.

[Claude Bash 샌드박스 적용 범위](https://code.claude.com/docs/en/sandboxing) · [내장 도구 권한](https://code.claude.com/docs/en/permissions)
