# 120. 라우터블 기술자산 검색 v1.8 — 찾기 → 발췌 (AI 토큰 절약)

작성: 2026-11-12 | 대상: Mac Studio | v1.7(8771)·v1.6(8770) 보존

## 목적
10GB 원본에서 필요한 1~2KB 조각만 빠르게 찾아 짧게 전달한다. 파일 전체를 읽지 않는다.

## 처음 한 번
- `~/Applications/라우터블 기술자산 검색 v1.8.app` 더블클릭 → `http://127.0.0.1:8772/`
- LaunchAgent `com.routabl.assetsearch.v18` 등록 → 로그인할 때마다 자동 실행, 쉬어도 꺼지지 않음 (127.0.0.1 전용)
- 해제: `launchctl bootout gui/$(id -u)/com.routabl.assetsearch.v18` 후 `~/Library/LaunchAgents/com.routabl.assetsearch.v18.plist` 삭제

## 실행 위치 (~/Library 밖)
- `~/ROUTABL-TechAssets/80_RUNTIME/ASSET_SEARCH_V1_8/`
  - `routabl_search_v1_8.py` — 색인기 + 서비스 한 파일 (이전 버전·~/Library에 의존하지 않음)
  - `index_v1_8.sqlite` — 조각 색인 (약 160MB)
  - `service.log`, `launcher.log`
- Claude가 원격으로 코드·색인을 갱신할 수 있음. 코드 파일이 바뀌면 서비스가 10초 안에 스스로 다시 시작

## AI 사용법 (내장 브라우저 또는 curl)
| 단계 | 요청 | 응답 크기 |
|---|---|---|
| 1. 찾기 | `GET /api/find?q=검색어&k=5[&scope=main|docs|gpt|working|variant|test|code]` | 1~2KB: 조각 ID·경로·줄·제목·자산ID·미리보기 |
| 2. 발췌 | `GET /api/chunk?id=조각ID[&n=1]` | 1~2KB: 원문 + 출처(경로:줄 @SHA, 자산ID). n=1이면 앞뒤 조각 포함 |
| 3. 줄 보기 | `GET /api/lines?p=경로&L=120-180` | 원본 파일의 줄 범위 (최대 120줄·4KB) |
| 상태 | `GET /api/status`, `GET /api/help` | |

- 여러 단어는 모두 포함(AND). 모두 포함이 없으면 하나라도 포함하는 조각을 많이 맞는 순으로
- 2글자 단어 가능. 별명: 정산·시니어·기사앱·고객등록앱·행정동·초성·주소록·분석앱·등록부·보안규칙 등
- 새로 고침: 화면의 **색인 새로 고침** 버튼 (변경된 파일만, 보통 1초 안팎)

## 검색 대상
- StudioProjects 전체 (주요 앱 6개 우선, Latest·archive·상단규격확정은 낮은 순위)
- 기술자산 00_GUIDE·30_REGISTRY(최신 등록부만, 자산 1건=조각 1개)·40_WORKING·60_AUDIT·70_EXPORTS·백서 PDF
- ChatGPT 공식 내보내기 대화 327개 (현재 흐름의 메시지 단위)
- 같은 내용의 파일은 대표본 하나만 조각으로 (중복 1,004개 제외)

## 보안 (키·비밀번호만 엄격히)
- 색인 제외 파일: 키스토어·인증서·개인키·.env·서비스 계정·client_secret·local.properties·keystore.properties 등 (현재 9개)
- 내용 가림: 개인키 블록, Google API 키, OpenAI/Anthropic 키, GitHub·Slack 토큰, AWS 키, OAuth 토큰, password/secret/token 대입값 → `[SECRET]`
- 가림은 파일 전체에 먼저 적용한 뒤 조각으로 나눔 (조각 경계에 걸친 키도 차단)
- 전화번호·이메일은 가리지 않음 (검색 용이성 우선, 사용자 결정 2026-11-12)
- 줄 보기는 StudioProjects·TechAssets 안만, 비밀 파일 이름은 거부, 경로 거슬러 오르기 거부

## 시험 결과 (2026-11-12, Claude 원격 셸, 실제 원본 읽기 전용)
- 색인: 파일 3,043개(대화 327 포함) / 조각 32,429개. 전체 생성 약 50초, 증분 새로 고침 0.34초
- 질문 10개 비교 (상위 5위 안 정답):
  - v1.8: 8/10 + 같은 결정을 담은 다른 정답 문서 1 / 놓침 1("업체명 호수" — 코드에 '호수'라는 단어가 없음)
  - v1.7: 3/10 (2단어 이상 한글 질문은 대부분 0건)
- 정답까지 읽는 양: v1.8 찾기+발췌 평균 약 2.9KB / v1.7 결과 JSON+파일 전체 평균 약 12.5KB (찾은 3건 기준)
- 찾기 속도 1~150ms
- Mac 실제 확인 (2026-11-12 09:03~09:05, 사용자가 앱 실행 → Claude 내장 브라우저):
  - LaunchAgent 등록·실행 (launcher.log, service.log)
  - 찾기 4~118ms, 응답 1.4~2.2KB / 발췌 1.3KB / 줄 보기 정상 / 자산 ID 표시
  - 원격 코드 갱신 → 10초 안 자동 재시작(CODE_CHANGED_RESTART → READY) 확인
  - Mac Python으로 색인 새로 고침 complete (새 파일 1개, 0.x초)
  - 수정: 2글자 검색 후보 400→5000, 제목·경로 일치 우선 (Mac SQLite에서 '초성' 정답이 잘리던 문제)
- 아직 확인 전: 재로그인·재시동 후 자동 시작

## 알려진 한계
- 단어 일치 방식: 다른 표현으로 쓰인 내용은 놓칠 수 있음 → 별명 추가, 필요하면 의미 검색(임베딩) 추가
- Mac에는 pdftotext가 없어 Mac 새로 고침에서는 새 PDF를 읽지 못함 (기존 PDF 조각은 유지). Claude 원격 셸에서 색인하면 포함
