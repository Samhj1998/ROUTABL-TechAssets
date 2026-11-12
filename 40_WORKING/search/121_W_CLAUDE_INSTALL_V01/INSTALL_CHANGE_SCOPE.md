# 설치 변경 범위

## 설치 직전

- 장치 ID와 hostname 일치. Homebrew 실행 경로 /opt/homebrew/bin/brew, 사용자 UID 501. prefix, bin, Caskroom, Cellar가 쓰기 가능했고 새 cask는 공식 정의에서 별도 종속성이 없었다.
- 기존 claude 명령, 대표 native/npm 경로 및 stable/latest cask 충돌 미발견. 공식 Homebrew API에서 arm64 단일 바이너리와 링크를 확인했고 로컬 homebrew-cask tap은 없었다.
- 원격 프로세스에서 ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, CLAUDE_CODE_OAUTH_TOKEN, ANTHROPIC_BASE_URL, CLAUDE_CONFIG_DIR 및 점검한 외부 제공자 변수는 미발견. 변수 값은 출력하지 않았다. Claude Desktop 표준 설정의 로컬 MCP 항목은 0. 유효 CLI MCP 목록은 별도 시험 대상이다.
- 초기 캐시 점검은 최상위 링크만 고려해 기존 ChatGPT 다운로드 한 건을 미참조로 잘못 분류했다. 이때 설치 호출은 실행되기 전에 중단됐다. Homebrew 7.0.11 cleanup.rb의 cache_files가 포함하는 Cask 폴더를 조사해 해당 다운로드의 링크를 찾았다. 정정한 점검에서 기존 다운로드 1개 중 미참조 0개였고, 정기 전체 정리 표식은 12.111일 경과로 기본 30일 기준 이내였다. 승인된 환경 변수 두 개로 설치를 실행했다.

## 설치 후

| 항목 | 전후 비교 |
|---|---|
| formula 수·버전 목록 | 1 → 1, 목록 SHA-256 동일 |
| cask 수·버전 목록 | 1 → 2, 추가 claude-code 2.1.309 한 건 |
| 기존 cask 목록 SHA-256 | stable cask를 제외하면 동일 |
| Homebrew 버전·Git HEAD | 7.0.11 · c6069d2a943b71b0a90d91fc1ac93cb9c1634dcc, 동일 |
| Node.js/npm | v24.21.0 · 11.19.0, 동일 |
| 기존 ChatGPT 다운로드 캐시 | 링크 존재, 750413801 B 확인 |
| Claude 설치 산출 | Caskroom 바이너리와 메타데이터, bin 링크, Homebrew 다운로드 캐시 |

점검한 설치 목록에서 예상 외 패키지 변경은 관측되지 않았다. 전체 파일시스템 감사나 로그인 셸·계정 설정 전수 검증은 범위에 포함되지 않았다.

[Homebrew 설치 및 정리 동작](https://docs.brew.sh/Manpage)
