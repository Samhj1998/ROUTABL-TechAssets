# 새 AI 작업 시작 안내 (기술자산 V1-6, 2026-11-14)

어느 AI(Claude·ChatGPT·Gemini)든 라우터블/Digitopia 작업을 시작할 때 이 1장만 먼저 읽는다.

## 1. 기술자산을 보는 관점 (사용자 확정 2026-11-14)
1. **공개 자료다.** 치명적 인증키·비밀번호와 남의 개인정보만 지키고 나머지는 철저히 개방.
2. **가치는 다음 프로젝트에서의 활용도다.** 자산 자체를 완벽하게 만드는 것이 목표가 아니다. 더 좋은 방법이 나오면 과감히 바꾸고, 그것을 다시 자산으로 삼는다.

## 2. 어디서 읽나
| 상황 | 방법 |
|---|---|
| 어디서든(웹·클라우드 AI) | GitHub 공개 저장소 https://github.com/Samhj1998/ROUTABL-TechAssets (읽기) |
| Mac 셸이 있을 때 | 검색 서비스 `http://127.0.0.1:8772`: `/api/find?q=검색어&k=5` → 고른 조각만 `/api/chunk?id=ID`. 파일 전체를 읽지 않는다 |
| 원본 위치 | Mac `~/ROUTABL-TechAssets`(git), 앱 코드 `~/StudioProjects/*` |

## 3. 먼저 볼 문서 (짧은 순)
1. `00_GUIDE/docs/guides/ROUTABL_CORE_AGENTS_COMMON_v1.0_20261113.md` — 라우터블 앱 공통 코어(초성검색 SEARCH-01, 데이터 받기 PERF-02, 주소록, 정산). **파생 앱은 기사앱 원본 코드를 그대로 쓴다**
2. `00_GUIDE/docs/principles/TECHASSETS_V1_COMPLETION_CRITERIA.md` — V1 완료 기준과 현재 상태
3. `30_REGISTRY/asset_manifest.json` — 자산 등록부(경로·SHA). 필요한 항목만 검색해서 본다

## 4. 규칙
- 텍스트는 `_vN` 사본을 만들지 않고 git 커밋으로 기록. 등록부는 파일 하나 + 이름표 `registry-v0.N`.
- 커밋하면 GitHub·NAS로 자동 백업(백업 v3 설치 후). 공개 저장소이므로 **키·비밀번호·고객 휴대번호·실제 거래 화면은 커밋 금지**(.gitignore 참조).
- 사용자 승인 필요: 삭제, 운영 Firebase 쓰기, 배포, 예약·권한 변경, 기존 자산 덮어쓰기.
- 결정 사항은 기록 전 한 줄로 확인받고, 사용자가 바꾸자고 할 때만 바꾼다.
- 보고: 실행한 것과 안 한 것을 구분. 단위 시험 PASS ≠ 실기기 PASS ≠ 운영 PASS.
- 백업 스크립트 6개(`00_GUIDE/ROUTABL_*Backup*`, `MacToNasOneShot`, `HeadlessDailyGate` 등)는 백업 v3 전환 승인 전까지 이동·수정 금지.

## 5. 작업이 끝나면
새로 얻은 기술·교훈은 짧은 문서로 커밋하고, 재사용할 핵심이면 등록부에 추가한다(무엇을·왜 바꿨는지·시험 근거·재사용 조건).
