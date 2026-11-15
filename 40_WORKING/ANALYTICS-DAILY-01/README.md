# ANALYTICS-DAILY-01 — 하루 분석 계산 규칙 1.0.0
Firebase 배차 원본 하나에서 갤럭시·Mac이 같은 계산값을 사용하고 UI만 다르게 만든다.
정답은 spec.json에 SHA-256으로 고정한 현행 Android Kotlin의 실제 실행 결과다.
포함: 입력 변환·완료/삭제·서울 날짜·금액·일/월/기간 합계·근무일·18만 원 이하 비율.
포함: dailySummaries 출퇴근·효율·시간대·의뢰지·영우/세원·달력 주 합계·과거 8주 같은 요일.
제외: Flow 결과 검증·수면·원인 분류·색상·레이아웃. 새 시험 데이터 제외 정책도 없다.
cases/의 합성 32개 입력과 expected.json을 두 앱의 계산 결과 비교에 사용한다.
today/nowMinute는 입력에 고정하며 실제 시계·Firebase·네트워크를 사용하지 않는다.
생성: `python3 40_WORKING/ANALYTICS-DAILY-01/tools/generate.py --write`
재현: `python3 40_WORKING/ANALYTICS-DAILY-01/tools/generate.py --check` → `byte diff 0`
Python은 입력 전달·JSON 직렬화만 담당하고 Kotlin 원본 8개를 그대로 컴파일한다.
FirestoreReader 변환부는 원문 추출, CalendarFragment 계산식은 최소 브리지로 구분한다.
로컬 kotlinc/Android Studio 번들 사용; `--kotlinc`·`--source-root`로 경로를 지정한다.
해시 불일치 시 중단한다. 변경 시 version·해시·입력 spec_version·기대값을 함께 갱신한다.
빌드 중간물은 tools/.build/에 보존·git 제외한다. 외부 저장소 쓰기·삭제·배포는 없다.
