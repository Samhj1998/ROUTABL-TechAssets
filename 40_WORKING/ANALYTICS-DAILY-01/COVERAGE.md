# ANALYTICS-DAILY-01 기능 대응표 (COVERAGE)

- 기준 결과표: `20261115_분석앱_전체기능_목록_결과표.md` §2, 표의 76개 기능 행(원본 줄 20–95).
- 기준 spec: `spec.json` v1.2.0. 결과표 본문에 적힌 v1.1.0/45 사례가 아니라 현재 규칙과 사례 파일을 대조했다.
- `화면 전용`은 계산 계약보다 UI·접속·상태·상호작용에 해당하는 항목이다. 부분 혼합 행은 계산/표시 계산의 사례와 화면 범위를 함께 적었다.
- `누락`은 계산 항목 중 spec 항목·사례로 연결되지 않는 경우에만 표기한다.

| 결과표 줄 | 기능 | spec 항목·사례 대응 |
|---:|---|---|
| 20 | 공통/로그인 — Google 로그인·계정 전환·로그아웃 | 화면 전용 |
| 21 | 공통/승인 확인 — 승인 계정 확인·승인 재시도 | 화면 전용 |
| 22 | 공통/화면 이동 — 5탭·좌우 스와이프 | 화면 전용 |
| 23 | 공통/기간 — 이번 달·지난달·사용자 기간·시간 탭 최근 3개월 | spec.extended.periods.presets; 46–53 (계산 규칙). 화면의 기간 선택/표시는 화면 전용 |
| 24 | 공통/데이터 받기 — 실시간 공유·캐시·서버 확인·오류 상태 | 화면 전용 |
| 25 | 요약 — 청구매출 KPI | spec.output.periodStats/monthStats; 01–14, 43–44, 54–56 |
| 26 | 요약 — 완료 배차 건수 KPI | spec.output.periodStats/monthStats; 01–03, 08–14, 43–44, 54–56 |
| 27 | 요약 — 기간 시간당 매출·출퇴근 유효일 수 | spec.rules.work_time/period; 15–20, 54–56 |
| 28 | 요약 — 기간 km당 매출·주행 기록일 수 | spec.compatibility_projection 및 periodStats; 15, 20, 54–56 |
| 29 | 요약 — 최근 6개월 월별 매출 추이 막대 | spec.extended.summary.monthly; 54–56 |
| 30 | 요약 — 이전 비교 기간 생성 | spec.extended.periods; 46–53 |
| 31 | 요약 — 청구매출/km당 증감률·배차 건수 증감 | spec.extended.summary.percentProbes; 54–56 |
| 32 | 요약 — 건당 평균 요금 비교 | spec.extended.summary; 54–56 |
| 33 | 요약 — 하루 평균 배차 건수 비교 | spec.extended.summary; 54–56 |
| 34 | 요약 — 평균 근무시간 비교 | spec.extended.summary; 54–56 |
| 35 | 요약 — 하루 주행거리 비교 | spec.extended.summary; 54–56 |
| 36 | 요약 — 수면·매출 비교 화면 진입 카드 | 화면 전용 |
| 37 | 캘린더 — 월 이동·날짜 선택·전날/다음날·날짜 유지 | 화면 전용 |
| 38 | 캘린더 — 월 청구매출 | spec.output.monthTotal/monthStats; 01–14, 27–29, 43–44 |
| 39 | 캘린더 — 월 완료 건수·근무일 수 | spec.output.monthStats; 01–14, 43–44 |
| 40 | 캘린더 — 근무일 하루 평균 매출 | spec.rules.denominators; 09–14, 43–44 |
| 41 | 캘린더 — 날짜별 매출·완료 건수 | spec.output.daily; 01–14, 43–44 |
| 42 | 캘린더 — 인접 월 포함 일~토 주 합계·건수 | spec.rules.calendar; 27–29, 44 |
| 43 | 그날 상세 — 청구매출·완료 건수 | spec.output.dayDetails.total; 01–14, 43–44 |
| 44 | 그날 상세 — 과거 8주 같은 요일 평균·당일 대비 증감률 | spec.rules.same_weekday; 30–32, 83 |
| 45 | 그날 상세 — 출근·퇴근·근무시간·오늘 실시간 경과 | spec.rules.work_time; 08, 15–20 |
| 46 | 그날 상세 — 시간당 매출 | spec.output.dayDetails.displayPerHour; 15–20 |
| 47 | 그날 상세 — 주행거리·km당 매출 | spec.compatibility_projection/dayDetails; 15, 20 |
| 48 | 그날 상세 — 비용·실질매출 | spec.rules.totals; 04–06, 08–14 |
| 49 | 그날 상세 — 시간대별 건수·매출·가장 바쁜 시간 | spec.rules.hourly; 25–26 |
| 50 | 그날 상세 — 연결·겹침·대기 횟수/총시간·대기 동·늦은 입력 | spec.output.dayDetails.flow; 33–42 |
| 51 | 그날 상세 — 의뢰지별 매출·건수 | spec.rules.customers; 21–24, 45 |
| 52 | 그날 상세 — 선택일 수면시간·미기록 표시 | spec.extended.sleep; 70, 74 |
| 53 | 하루 배차목록 — 완료 배차 시각순·상세 필드 표시 | spec.extended.dayDetails; 81 |
| 54 | 하루 배차목록 — 배차 사이 대기 삽입·위치·시각 없는 배차 | spec.extended.dayDetails; 82 |
| 55 | 하루 배차목록 — 전후 날짜 버튼·스와이프·미래 제한 | 화면 전용 |
| 56 | 고객 — 의뢰지별 매출·건수 순위 | spec.extended.customerGroups; 57–59 (requester) |
| 57 | 고객 — 출발지별 매출·건수 순위 | spec.extended.customerGroups; 57–59 (dept) |
| 58 | 고객 — 도착지별 매출·건수 순위 | spec.extended.customerGroups; 57–59 (dest) |
| 59 | 고객 — 고객 수·상위 3곳/나머지·항목별 매출 비중 | spec.extended.customerGroups; 57–59 (shares) |
| 60 | 고객 — 이전 기간 고객별 증감·신규 판정 | spec.extended.customerGroups; 57–59 |
| 61 | 고객 상세 — 선택 고객 최근 6개월 매출 | spec.extended.customerGroups; 60, 62 (months) |
| 62 | 고객 상세 — 자주 가는 구간 상위 5개 | spec.extended.customerGroups; 61–62 (routes) |
| 63 | 고객 상세 — 결제 방법별 건수 | spec.extended.customerGroups; 61–62 (payments) |
| 64 | 고객/목록 — 상위 10곳·전체 보기·접기·상세 대화상자 | 화면 전용 |
| 65 | 시간 — 요일×시간대 배차 건수 히트맵 | spec.extended.time.counts/rowTotals; 63–65 |
| 66 | 시간 — 가장 몰리는 요일·시간 상위 3개 | spec.extended.time.top; 63–65 |
| 67 | 시간 — 요일별 근무일 하루 평균 매출·근무일 수 | spec.extended.time.weekdayAverages; 64–65 |
| 68 | 시간 — 날짜별 출퇴근·근무시간·시간당·km당 매출 | spec.output.workDays; 08, 15–20, 54–56 |
| 69 | 시간/목록 — 최근 3개월 기본·날짜 10개/전체·일요일 조건부 표시 | 화면 전용 |
| 70 | 경로 — 출발지→도착지 구간 수·횟수 순위 | spec.extended.routes; 66–67 |
| 71 | 경로 — 구간별 평균 요금·주 차량 | spec.extended.routes; 66–67 |
| 72 | 경로 — 연결운행 비율·분자/분모 | spec.extended.flowDisplay; 68–69 |
| 73 | 경로 — 겹친 운행 비율·횟수 | spec.extended.flowDisplay; 68–69 |
| 74 | 경로 — 20분+ 대기 횟수·평균 시간 | spec.rules.flow; 33–42, 68–69 |
| 75 | 경로 — 대기 동 순위·횟수·평균·위치 누락/늦은 입력 | spec.extended.flowDisplay; 37–42, 69 |
| 76 | 경로/목록 — 구간 상위10/전체 보기·기간 선택 | 화면 전용 |
| 77 | 수면 — Health Connect 권한·이력·설치/업데이트·다시 읽기·상태 안내 | 화면 전용 |
| 78 | 수면 — 서울 기상일에 수면 귀속·하루 다회 합산 | spec.extended.sleep.sessions; 70 |
| 79 | 수면 — 로컬 ID 중복/변경/삭제 병합·토큰 만료 재조회 | spec.extended.sleep.cache; 71–72 |
| 80 | 수면·바닥방어 — 18만 원 이하 근무일 비율·일수·금액 미확인 제외 | spec.rules.denominators/floorReport; 09–14, 43–44 |
| 81 | 수면 — 수면 미기록 근무일 수 | spec.extended.sleep.missing; 74 |
| 82 | 수면 — 수면 구간별 일수·평균 매출·18만 원 이하 비율 | spec.extended.sleep.groups; 73–74 |
| 83 | 수면 — 날짜별 매출·수면 추이 및 미기록 구간 단절 | spec.extended.sleep.trend; 76 |
| 84 | 수면 — 저매출일 퇴근·파트너 매출·선택기간 평균 | spec.output.floorReport; 15–16, 23–24, 54–56 |
| 85 | 수면 — 저매출일 원인 분류 | spec.extended.sleep.causes; 75 |
| 86 | 메인 배너 — 평일 수면 시간 안내·상태 구분·화면 연결 | 계산: spec.extended.sleep.banner 77–80; 배너 표시/색/연결: 화면 전용 |
| 87 | 수면 권한 안내 — 사용 목적·권한 철회·기존 기능 안내 | 화면 전용 |
| 88 | 설정 — 계정 표시·앱 버전·로그아웃 | 화면 전용 |
| 89 | 설정 — 새로고침·마지막 동기화·캐시/실패 상태 | 화면 전용 |
| 90 | 설정/데이터 점검 — 건수·기간·출퇴근 기록일 점검 | spec.output.quality/qualityDisplay; 01–08, 12–14, 43–44, 87 |
| 91 | 내보내기 — 기간·자료 선택·CSV/XLSX 생성·공유 | 화면 전용 |
| 92 | 내보내기/일자별 — 무배차일 포함 일별 15열 | spec.extended.exports; 84 (daily) |
| 93 | 내보내기/고객별 — 의뢰지 순위·매출·비중 | spec.extended.exports; 86 (customer) |
| 94 | 내보내기/요일×시간 — 7×24와 행 합계 | spec.extended.exports; 86 (heatmap) |
| 95 | 내보내기/배차 원본 — 완료 전·삭제 포함 원본 20열 | spec.extended.exports; 85, 87 (raw) |

**대응 없는 계산 행: 0개.**
