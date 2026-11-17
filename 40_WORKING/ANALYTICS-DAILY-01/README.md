# ANALYTICS-DAILY-01 — 하루 분석 계산 규칙 1.1.0
Firebase 배차 원본 하나에서 갤럭시·Mac이 같은 계산값을 사용하고 UI만 다르게 만든다.
정답은 제외 전처리 후 입력을 spec.json에 SHA-256으로 고정한 현행 Android Kotlin에 넣은 실제 실행 결과다.
포함: 입력 변환·완료/삭제·서울 날짜·금액·일/월/기간 합계·근무일·18만 원 이하 비율.
포함: dailySummaries 출퇴근·효율·시간대·의뢰지·영우/세원·달력 주 합계·과거 8주 같은 요일.
포함: Flow 대기(앞 완료→다음 배차 20분 이상)·겹침·연결·WaitPlace 위치 판정.
거래처 키는 `requester.trim()` 완전 일치, 주요 거래처는 고객 목록 이름 그대로 `[영우티엔에프, 세원텍스, 빠른발]`이다.
현행 Kotlin 영우/세원 합산의 포함 매칭은 유지하며, 위 이름에서 완전 일치 합과 같음을 사례 45로 확인한다.
제외: 수면·원인 분류·색상·레이아웃·timeline 표시 문구.
cases/의 합성 45개 입력과 expected.json을 두 앱의 계산 결과 비교에 사용한다.
기존 32개 + 흐름 10개(33~42) + 제외 적용 2개(43~44) + 거래처 이름 1개(45).
`exclusions.json`은 갤럭시·Mac 공통이며 현재 `dispatchDate=2026-10-09, totalFare=84` 조건 1개다. **추가는 사용자 확인 후**.
형식은 `{dispatchDate, totalFare, documentId?}`. 날짜와 금액이 모두 같고, 선택적 문서 ID가 있으면 그것도 완전 일치해야 제외한다.
단건 변환으로 dispatchTime의 서울 날짜·금액을 판정한 뒤 모든 집계 전에 입력에서 뺀다. ID 미지정이면 같은 날짜+금액 모두에 적용한다.
Kotlin 원본에는 이 필터가 없다. 생성기 Kotlin 브리지의 별도 전처리이며, 필터 후 자료만 원본 집계에 전달한다.
사례 43은 시험 건 제외로 근무일·18만 이하 비율의 분모가 바뀌고, 44는 근접 불일치 자료 보존과 흐름·달력·요일 반영을 검증한다.
today/nowMinute는 입력에 고정하며 실제 시계·Firebase·네트워크를 사용하지 않는다.
생성: `python3 40_WORKING/ANALYTICS-DAILY-01/tools/generate.py --write`
재현: `python3 40_WORKING/ANALYTICS-DAILY-01/tools/generate.py --check` → `byte diff 0`
Python은 입력 전달·JSON 직렬화만 담당하고 Kotlin 원본 8개를 그대로 컴파일한다.
FirestoreReader 변환부는 원문 추출, CalendarFragment 계산식은 최소 브리지로 구분한다.
로컬 kotlinc/Android Studio 번들 사용; `--kotlinc`·`--source-root`로 경로를 지정한다.
해시 불일치 시 중단한다. 규칙 변경 시 version·입력 spec_version·기대값을 갱신하며 원본 변경이 있을 때만 검토 후 해시를 갱신한다.
빌드 중간물은 tools/.build/에 보존·git 제외한다. 외부 저장소 쓰기·삭제·배포는 없다.

수면 공유(계산 범위 밖, 기록용 2026-11-17): 폰 분석앱이 `users/{uid}/sleepDaily/{yyyy-MM-dd} = {hours, updatedAt}`로 깬 날짜별 합계만 올린다(앱 열 때 + 매일 11시 WorkManager, 백그라운드 읽기 권한 필요). Mac은 이를 그날 00:00:01(서울)에 끝난 세션으로 바꿔 같은 수면 규칙에 넣는다. 2026-11-17 SleepReader·MainActivity 해시 갱신: 올리기·예약만 바뀌고 계산 변화 없음(--check 87사례 diff 0).
