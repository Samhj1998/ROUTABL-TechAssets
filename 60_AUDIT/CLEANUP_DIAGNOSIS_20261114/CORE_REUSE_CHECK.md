# 공통 코어 재사용 점검 (2026-11-14, 읽기 전용)

기준: `ROUTABL_CORE_AGENTS_COMMON_v1.0` — 파생 앱은 기사앱(`~/StudioProjects/DISPATCH-One-Android`, 최근 커밋 6e36dbde 11-13) 코어를 원본 그대로 쓴다. 비교는 패키지·import 줄을 뺀 내용 기준.

| 코어 | 시니어앱 | 분석앱 | 고객등록앱 |
|---|---|---|---|
| SEARCH-01 KoreanSearch·Adapter | 동일 | 동일 | 동일 |
| 정산 SettlementRules | 동일 | 동일 | 동일 |
| PERF-02 LatestScreenWork·ScreenWorkers | 동일 | 동일(출처 주석 1줄만 추가) | 해당 없음 |
| PERF-02 DriverDispatchRepository | **기사앱보다 한 단계 뒤처짐** | 클래스 없음 — 자체 `FirestoreReader`(리스너+캐시 방식) | 해당 없음 |
| CUSTOMER-DIR CustomerCache | 동일 | 해당 없음 | 동일 |
| CUSTOMER-DIR CustomerDirectory | 동일 | 해당 없음 | 의도적 변경(권한 확인을 고객등록앱 승인 방식으로, `[고객등록앱]` 주석) |

## 발견 1 — 시니어앱 수정 누락 (조치 필요, 승인 후)
- 기사앱 `DriverDispatchRepository.listen()`에는 `skipInitialSnapshot` 처리가 있음: 저장 직후 **저장 전 옛 목록이 잠깐 다시 보이는 현상**을 막는 수정.
- 시니어앱에는 이 수정이 없음(5줄 차이). 시니어앱에서 배차 저장 직후 목록이 잠깐 이전 상태로 깜빡일 수 있음(실기기 미확인).
- 제안: 기사앱 파일을 시니어앱에 그대로 반영(호출부 1곳 확인) → 빌드·실기기 확인. 운영 앱 변경이라 승인 필요.

## 발견 2 — 분석앱 데이터 받기는 원본 클래스가 아님 (확인 필요)
- 11-13 기록은 "분석앱을 PERF-02로 교체(416a390)". 실제로는 `DriverDispatchRepository`가 아니라 자체 `FirestoreReader`가 리스너·캐시를 직접 다룸.
- 규칙("원본 코드 그대로")과 다르므로, 의도된 예외인지 사용자 확인 후 규칙 문서에 예외로 기록하거나 원본 클래스로 교체.

## 발견 3 — CUSTOMER-DIR 변경분 수신은 안전 (점검 후보 해제)
- `changedAt >= 커서`(같은 시각 재수신 허용, 재적용해도 결과 동일), 정렬 `changedAt → id`, 삭제 표시(`deleted`), 변경 기록 컬렉션 + 실시간 리스너 구조.
- DK 검토에서 걱정한 "같은 시각 다건 누락"을 이미 겹침 재수신으로 막고 있음 → **결함 아님**.
- 오히려 DK(용어사전) 동기화 설계에 그대로 재사용할 만한 검증된 자산: 변경 기록 + `>=` 커서 재수신 + 멱등 적용 + 삭제 표시.
