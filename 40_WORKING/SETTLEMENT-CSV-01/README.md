# SETTLEMENT-CSV-01 — 정산 CSV 규칙 1.0.0
기사앱 Kotlin과 Mac 분석 웹앱 JS가 동일 입력에서 같은 CSV 바이트 또는 오류 코드를 내도록 고정한다.
기준 루트 D: `~/StudioProjects/DISPATCH-One-Android` (읽기 전용).
기준: `D/shared/kotlin/com/routivel/shared/SettlementRules.kt:10–73` — 포함·날짜·금액·결제.
기준: `D/shared/kotlin/com/routivel/shared/SettlementCsv.kt:9–78` — 열·검증·정렬·합계·이스케이프.
호출: `D/app/src/main/java/com/routivel/driver/DispatchExportController.kt:281–313`, `DriverSettlement.kt:13–18`.
기존 시험 참조: `D/shared/test/com/routivel/shared/SettlementRulesTest.kt:12–81` (실데이터 문자열은 복사하지 않음).
규칙이 바뀌면 `spec.json`의 version을 올리고 원본 해시·입력 spec_version·기대 사례를 함께 재생성한다.
양쪽 구현은 `cases/*.input.json` 전체에 대해 기대 CSV 바이트(BOM·LF 포함) 또는 기대 오류 코드를 통과해야 한다.
생성: `python3 40_WORKING/SETTLEMENT-CSV-01/tools/generate.py --write` (저장소 루트에서 실행).
재현 검증: `python3 40_WORKING/SETTLEMENT-CSV-01/tools/generate.py --check` → `byte diff 0`.
Python은 JSON을 Kotlin 입력으로 전달하며, 기대 CSV는 원본 Kotlin 두 파일을 실제 컴파일·실행해 만든다.
로컬 kotlinc/Android Studio 번들을 사용하며 `--kotlinc`, `--source-root`로 경로 지정 가능; 원본 해시 불일치는 중단한다.
오류 코드는 원본 예외를 정규화한 사례 계약이며 Kotlin 자체 코드가 아니다; 필터 후 0건도 CSV 출력 거부다.
가짜 데이터만 사용한다. 빌드 중간물은 `tools/.build/`에 보존·git 제외하며 외부 저장소 쓰기·네트워크 접근은 없다.
