# PERF-02 핵심 재사용 자산 등록 (2026-11-13, 레지스트리 v0.36)

## 사건
분석앱(11/11 제작)이 기사앱의 데이터 받기 방식을 원칙만 가져와 새로 구현(JSON 캐시, 새로고침 때만 서버 읽기) → 11/11(수) 배차가 캘린더에 반영되지 않음.

## 원인
1. 기사앱 DriverDispatchRepository(리스너 공유·폰 캐시)가 기술자산에 등록되지 않음 (검색 0건)
2. PERF-01 정의가 LatestScreenWork·ScreenWorkers(캐시 우선 표시)만 포함, 데이터 수신 방식 누락
3. 공통코드 복사(shared/)는 Firebase 무관 로직만 대상, 데이터층은 app/ 안이라 복사 범위 밖
4. 파생 앱 제작 시 기사앱 방식과 대조하는 확인 단계 없음

## 조치
- 분석앱 PERF-02 적용(416a390) → 실기기 자동 갱신 확인(테스트 오더 2건), 화면 뒤 계산·스와이프·당일 리포트 추가
- 기사앱 1.0.70 / 시니어앱 1.0.22: 입력 시각·입력 위치(대기 동), 관제 위치 공유 항상/필요시(기기별)
- ANALYTICS-APP-01-LOCAL-CACHE → 비권장(SUPERSEDED_BY_PERF-02__DO_NOT_REUSE)

## 규칙 (v0.36부터)
파생 앱은 Firebase 배차 데이터를 PERF-02 코드 그대로 받는다. 원칙만 재사용하거나 새로 짜지 않는다. 바꿔야 하면 이유를 기록하고 사용자 확인.

파생 앱 체크리스트: 데이터 받기(PERF-02) · 화면 뒤 계산(LatestScreenWork·ScreenWorkers) · 검색(SEARCH-01) · 정산 규칙(SettlementRules) · 화면 이동(UX-SWIPE-01) · 안 쓴 항목의 이유

## 등록 자산
| asset_id | 내용 | 검증 | sha256 |
|---|---|---|---|
| PERF-02-DRIVER-DISPATCH-REPOSITORY | [표준] 배차 데이터 받기: 실시간 리스너 1개를 모든 화면이 공유 + Firestore 폰 캐시, 화면이 모두 떠나면 1초 뒤 해제 (기사앱 원본) | FIELD_PROVEN_DRIVER_APP_100_UPDATES | 9ebb1ebc8e00 |
| PERF-02-LATEST-SCREEN-WORK | [표준] 화면 뒤 계산·최신 요청만 반영 LatestScreenWork (기사앱 원본) | FIELD_PROVEN_DRIVER_APP_100_UPDATES | f2aa744aeb98 |
| PERF-02-SCREEN-WORKERS | [표준] 계산 스레드·UI 실행기 ScreenWorkers (기사앱 원본) | FIELD_PROVEN_DRIVER_APP_100_UPDATES | 586fe799d908 |
| PERF-02-ANALYTICS-APPLIED-REPOSITORY | PERF-02 파생앱 적용 예: 분석앱 AnalyticsRepository (리스너 공유·화면 뒤 Insights 1회 계산) | DEVICE_USE_PASS_USER_OBSERVED_AUTO_UPDATE_2_TEST_ORDERS | 757daa20e428 |
| PERF-02-ANALYTICS-APPLIED-READER | PERF-02 파생앱 적용 예: 분석앱 FirestoreReader.listenAll (읽기 전용, MetadataChanges.INCLUDE) | DEVICE_USE_PASS_USER_OBSERVED_AUTO_UPDATE_2_TEST_ORDERS | 1b5f5365dae2 |
| UX-SWIPE-01-DRIVER | [표준] 좌우 스와이프 화면 이동 SwipeNavigationUtils (72dp, 가로≥세로×1.35, 입력칸 제외) | FIELD_PROVEN_DRIVER_APP | e7536b194dee |
| UX-SWIPE-01-FRAGMENT-TABS | UX-SWIPE-01 Fragment 탭용 이식본 SwipeTabs (취소 신호 보강) | DEVICE_USE_PASS_USER_OBSERVED | 7d267826baf7 |
| DATA-02-INPUT-LOCATION | 배차 입력 순간 위치=대기 위치(입력 시각·좌표·가장 가까운 주소록 동) + 관제 위치 공유 항상/필요시(기기별) | INSTALLED_DRIVER_1.0.70_SENIOR_1.0.22__FIELD_TEST_PENDING | 6d8e7a371fd4 |
| ANALYTICS-APP-01-WAIT-PLACE | 분석앱 대기 장소 판정 WaitPlace (늦은 입력: 출발지 300m 또는 입력→픽업 3분) | INSTALLED__FIELD_TEST_PENDING | a8201df1fa84 |
| ANALYTICS-APP-01-DAY-REPORT | 분석앱 당일 리포트(퇴근 전 실시간)·하루 배차목록(대기·적요) | DEVICE_USE_PASS_USER_OBSERVED | 7c7c47bc3dfa |

## 파일
- asset_manifest_v0.36.json (= asset_manifest.json), asset_120_lookup_v0.22.sqlite (로컬 작업 폴더에서 생성 후 복사)
- 이전판 v0.35 / v0.21 → _archive_versions/
