# 라우터블 앱 공통 안내 원본 (각 앱 AGENTS.md에 같은 내용)

적용: DISPATCH-One-Android, ROUTABL-Senior-Driver, ROUTABL-Analytics-Android, ROUTABL-CustomerRegistration-Android (각 폴더 AGENTS.md + CLAUDE.md)
고치면 네 앱의 AGENTS.md 공통 부분도 같이 고칩니다.

## 라우터블 공통 코어 (모든 라우터블 앱 공통 · v1.0 2026-11-13)

기사앱(`~/StudioProjects/DISPATCH-One-Android`)이 현장에서 검증된 원본(어머니 앱)입니다.
파생 앱은 아래 코어를 **원본 코드 그대로** 씁니다. 원칙만 가져와 새로 짜지 않습니다.
바꿔야 하면 이유를 인계 메모에 적고 사용자에게 먼저 확인합니다.
(2026-11-11 분석앱이 데이터 받기를 새로 짜서 배차 누락이 난 사례가 있어 만든 규칙입니다.)

| 영역 | 자산 ID | 원본 (기사앱 `app/src/main/java/com/routivel/driver/`) |
|---|---|---|
| 배차 데이터 받기 | PERF-02 | `DriverDispatchRepository.kt` — 리스너 1개 공유 + Firestore 폰 캐시, 화면이 모두 떠나면 1초 뒤 해제 |
| 화면 뒤 계산 | PERF-02 | `LatestScreenWork.kt`, `ScreenWorkers.kt` — 무거운 계산은 화면 뒤에서, 최신 요청만 반영 |
| 고객 주소록 | CUSTOMER-DIR | `CustomerDirectory.kt`, `CustomerCache.kt` — changedAt 기준 변경분만 받기 |
| 초성 검색 | SEARCH-01 | `shared/.../KoreanSearch.kt`, `KoreanSearchAdapter.kt` |
| 정산·매출 규칙 | — | `shared/.../SettlementRules.kt` (완료만, 삭제 제외, 금액 모르면 "금액 확인 필요") |
| 화면 이동 | UX-SWIPE-01 | `SwipeNavigationUtils.kt` — 72dp, 가로≥세로×1.35, 입력칸 위 제외, 왼쪽=다음 |
| 입력 위치·관제 공유 | DATA-02 | `DeviceLocationSettings.kt` — 기기별 설정, 입력 순간 위치=대기 위치 |
| 동 이름 | DATA-01 | 배차 당시 저장된 동(스냅샷). 기준은 인성데이타·주소록. 카카오 행정동은 쓰지 않음 |

- `shared/`는 고치지 않고 통째 복사합니다. 해시는 `SHARED_SOURCE.md`, 빌드 검사 `verifySharedHash`.
- 기술자산 등록부: `~/ROUTABL-TechAssets/30_REGISTRY/asset_manifest.json` (검색 DB `asset_120_lookup_*.sqlite`). 새 코어가 생기면 등록합니다.

### 새 기능·새 앱 체크리스트
1. 데이터 받기는 PERF-02인가
2. 무거운 계산은 화면 뒤(LatestScreenWork·ScreenWorkers)인가
3. 검색은 SEARCH-01, 정산은 SettlementRules 그대로인가
4. 화면 이동은 UX-SWIPE-01 기준인가
5. 안 쓴 항목이 있으면 이유를 인계 메모에 적었는가

## 작업 방식
- 요구사항과 화면 구성은 사용자 확인 후 코드로 옮깁니다. 현장 판단(업무 흐름·예외 상황)은 사용자 기준이 우선입니다.
- Claude가 수정·분석하고, 사용자가 Mac의 Android Studio에서 빌드·설치·커밋·푸시합니다. 원격 셸에서는 git commit을 하지 않습니다(잠금 파일 문제).
- 작업이 끝나면 `docs/` 인계 메모에 무엇을 왜 바꿨는지 짧게 남깁니다.
- 결과는 간결하고 빠르고 정확하게, 토큰을 적게 쓰는 방향으로.
