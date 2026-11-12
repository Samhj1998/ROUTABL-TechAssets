# 200. 라우터블 분석앱 기술자산 등록 기록 v1.0

- 작성: 2026-11-11 KST, Claude 세션 (사용자 승인 후 B등급 작업)
- 대상 앱: 라우터블 분석 (`com.routivel.analytics`) 0.1.0
- 소스 위치: `/Users/yongho/StudioProjects/ROUTABL-Analytics-Android` (git 로컬 저장소, GitHub 미등록)
- 등록부: `asset_manifest_v0.28.json` (v0.27 내용 무변경 + 분석앱 자산 추가), 검색 색인: `asset_120_lookup_v0.14.sqlite` (v0.13 복사 + 추가)

## 1. 배경과 계보

- 97-1 봉인본 `13_지속갱신_기술자산등록부.tsv`의 `ANALYSIS-APP-FUTURE`(계획 단계·미구현)를 구현한 결과입니다.
- 봉인본은 수정하지 않았습니다. 새 자산의 `parent_asset_ids`로 `ANALYSIS-APP-FUTURE`와 재사용한 기존 자산을 연결합니다.
- 분석앱은 기사앱(DISPATCH-One-Android b9c40c2, 1.0.68)을 건드리지 않는 **독립 앱**입니다. (VI-01: 기사앱 `shared/`는 링크가 아니라 무수정 복사, 확인값은 `SHARED_SOURCE.md`)

## 2. 기존 자산 재사용 실태 (있는 그대로)

| 기존 자산 | 재사용 방식 |
|---|---|
| 기사앱 `shared/SettlementRules` (정산 날짜·포함·금액 규칙) | 코드 무수정 복사. 모든 집계의 기준 |
| 기사앱 `FixedFontActivity` | 코드 복사 (글자 100% 고정, 화면 밀도는 기기 설정) |
| 기사앱 월간정산 주간합계 방식 | 규칙 재현 (일~토, 토요일 칸 주계, 달 경계 7일 합산) |
| AUTH-01 | 원칙 재사용, 코드 재작성 (Google 로그인 + users/{uid}.approved) |
| DATA-01 | 원칙 재사용 (배차 당시 동·장소 스냅샷 우선, 현재 주소록으로 덮어쓰지 않음) |
| PERF-01 | 원칙만(캐시 우선 표시). `LatestScreenWork`·`ScreenWorkers` 코드는 사용하지 않음 |
| SEARCH-01 | `shared/`에 함께 복사되었으나 분석앱 화면에서 사용하지 않음 |

## 3. 새로 등록하는 자산

| asset_id | 내용 | 검증 상태 |
|---|---|---|
| ANALYTICS-APP-01-READONLY-BUILD-GUARD | Firestore 쓰기 코드가 있으면 빌드 실패 (`verifyReadOnlyFirestore`) | 사용자 Mac 빌드 성공, 일부러 위반시키는 시험은 미실시 |
| ANALYTICS-APP-01-FIRESTORE-READER | Firestore 접근 유일 파일, `get(Source.SERVER)`만 사용 | 실기기 로그인·불러오기 성공 |
| ANALYTICS-APP-01-LOCAL-CACHE | 한 번 읽어 앱 전용 JSON 저장, 새로고침 때만 서버 재조회 | 실기기 사용 확인 |
| ANALYTICS-APP-01-DAILY-STATS | 기사앱 정산 규칙 위 일별·월별 집계 | 2026-08-01~11-11 기사앱과 103일·4개월·11월 135건 전부 일치 |
| ANALYTICS-APP-01-INSIGHTS | 기간 비교·고객 순위·요일×시간대·근무효율·구간 | 화면 숫자 사용자 확인(11월 일부), 전체 대조는 미실시 |
| ANALYTICS-APP-01-XLSX-WRITER | 외부 라이브러리 없는 .xlsx/CSV 작성 | 실기기 내보내기 → 카카오톡 전달 → 엑셀 열람, 일자별 시트 = 캘린더 |
| ANALYTICS-APP-01-FLOW-RULES | 연결운행·겹친 운행·대기(동 단위, 20분) | 규칙 확정은 사용자, 단위 시험 미실행 |
| ANALYTICS-APP-01-FLOW-TEST | Flow 단위 시험 (예시 5건 + 20분 경계) | 기대값만 파이썬 재계산으로 대조, Gradle 실행 미실시 |
| ANALYTICS-APP-01-SHARED-SOURCE | `shared/` 복사 출처·SHA 기록 | 기사앱 원본과 SHA 일치 확인 |
| ANALYTICS-APP-01-VERIFICATION-REPORT / -SCRIPT | 두 앱 내보내기·월간정산 대조 기록과 스크립트 | 2026-11-11 실행 결과 기록 |
| ANALYTICS-APP-01-README | 앱 목적·읽기 전용 원칙·빌드 방법 | 문서 |

## 4. 하지 않은 것

- 기존 등록부 v0.27, 색인 v0.13, 97-1 봉인본, NAS 백업, `~/Library`의 자산 검색 서비스 DB: **변경 없음**
- 따라서 자산 검색 앱(v1.5)에서는 사용자가 색인을 다시 만들기 전까지 새 항목이 보이지 않습니다.
- `google-services.json`(API 키 포함)은 등록하지 않았습니다. (보안 규칙 4)
- 운영 Firebase, 기사앱 코드: 변경 없음

## 5. 남은 확인

- 분석앱 단위 시험(DailyStats·Insights·Flow·ExportTables)을 Android Studio에서 실행
- 읽기 전용 검사를 일부러 위반시켜 빌드가 실패하는지 확인
- 분석앱 저장소 GitHub 등록(원하면) 및 NAS 백업 범위 포함 여부 결정
- '너네집' 12원·6원 테스트 자료 115건(9/1~10/9) 일괄 삭제 후 분석앱 새로고침
