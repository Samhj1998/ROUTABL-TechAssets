# 전체 프로세스 격리 방식

장치 MacStudioui-MacStudio.local, arm64, UID 501. Claude Code Homebrew stable 2.1.309.

| 방식 | 경계와 현재 판정 |
|---|---|
| Anthropic sandbox-runtime 외부 래퍼 | 전체 대상 프로세스와 자식에 OS 정책을 적용하는 1순위 후보. 별도 패키지가 필요하며 Keychain·프로세스 실행·프록시 호환성은 NOT_TESTED |
| 직접 macOS Seatbelt | 기존 도구로 외부 래퍼의 일부 동작을 합성 Python에서 검증. 표준 입력 상속·파일·로컬 소켓 시험 PASS. 네이티브 Claude, 실제 인증 및 관리 가능한 온라인 프록시는 NOT_TESTED |
| 별도 macOS 표준 사용자 | 분리된 홈·자격증명·계정이 장점. 기존 홈/공유·NAS 마운트의 읽기, 접근 가능한 그룹·ACL 및 네트워크는 별도로 제한·검증해야 함. 계정 생성, 별도 경로, OAuth 승인 필요 |
| 폴더만 분리 | C1 FAIL 재현 |
| Claude 내장 Bash 샌드박스 | 셸 자식용 추가 경계. 내장 Read/Edit/Write와 MCP/hooks 등의 전체 프로세스 경계는 별도 |

1순위는 고정 버전 srt를 전용 경로에 설치할 별도 승인을 받은 뒤, 같은 구성의 무호출 검증으로 진행하는 것이다. Keychain 사용에 광범위한 홈 접근 또는 IPC 허용이 필요해지면 별도 표준 사용자와 검증된 프로세스·네트워크 경계의 조합을 검토한다.

[Anthropic Sandbox Runtime](https://github.com/anthropics/sandbox-runtime) · [Claude Bash와 다른 도구의 경계](https://code.claude.com/docs/en/sandboxing)
