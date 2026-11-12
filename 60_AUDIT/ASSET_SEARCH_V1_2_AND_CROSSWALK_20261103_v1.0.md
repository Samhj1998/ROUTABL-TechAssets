# 120. 기술자산 통합검색 v1.2 · Mac/NAS/GitHub 원본 계보 검증
확인 시각: 2026-11-03T10:40:56+09:00
범위: 읽기 전용 원본 조사, 신규 전용 검색엔진·DB·자산대장 생성. 원본/Firebase/GitHub/NAS 원본/기존 예약 설정 변경 없음.

## 원인 및 수정
기존 v1.1 검색은 /Volumes/Dev_Assets/Routabl만 인덱싱하여 Mac StudioProjects 원본을 누락함.
v1.1 스크립트, 웹 UI, assets.sqlite 2270개 행은 그대로 보존.
신규 v1.2: routabl_assetsearch_v1_2.py, routabl_web_v1_2.py, assets_v1_2.sqlite.
v1.1 DB를 SQLite backup API로 신규 DB에 복제 후, 명시한 2개만 메타데이터 색인. DB 2272개, PRAGMA integrity_check=ok.
색인에는 원문 내용을 저장하지 않음(content 길이 0); 확장 탐색 또는 소스코드 실행 없음.
검색 키워드 cloud_access.py 1개 실제 Mac 경로 조회 성공; UI HTTP / 및 /api 테스트 통과 후 서버 종료.

## TA-CASE-20261102-01
Mac 원본: /Users/yongho/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py
SHA256: de08b060d03a6b6c9f155cf89673f2285a67502cf664442b1a9bc835529a54e5
GitHub private Samhj1998/DISPATCH-One-Android/tools/firebase-migration/cloud_access.py
Git blob: 28d29626d2adf4e2df81cf889b32693d710dcc60, Mac Git와 동일함.
일반 NAS 아카이브에 독립 원본 파일 미발견. 신규 소스파일 자동 백업 범위 외부.
Firebase 현재 실행/등록 시험은 수행하지 않음.

## INTEGRATION-F1
Mac 원본: /Users/yongho/StudioProjects/DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt
SHA256: 5494734c4599b051c545523ed9142c52919c21d5d04bdd4f8dc3436dd41d8e03
NAS 사본: /Volumes/Dev_Assets/Routabl/ROUTABL_Whitepaper_Archive_20261101/03_TECH_ASSETS/Source_Evidence/DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt
NAS SHA256: 5494734c4599b051c545523ed9142c52919c21d5d04bdd4f8dc3436dd41d8e03 (Mac과 동일)
GitHub private Samhj1998/DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt
Git blob: c3b8c51e1968955619b4a822ad604fdc04b76648 (Mac Git와 동일)
정적 소스/파일 동일성만 확인. APK 또는 Firestore Rules 최신 동작은 검증하지 않음.

## 자산대장
asset_manifest_v0.4.json 생성, 기존 0.3 보존. v0.3의 선택 10개 자산 SHA256 재검증 10/10 일치.
신규 자산 3개(검색 스크립트, 별도 DB, 별도 웹 UI)와 계보 2건 등록.
기존 2270건은 NAS 범위 중심이며 실사용 가능한 Mac 전체 통합 인덱스라고 과장하면 안 됨.

## 위험 및 다음 선택
Mac StudioProjects 나머지는 명시적으로 색인하지 않음(보안과 개인정보).
현재 기술자산 AES 이미지 백업 범위는 ~/ROUTABL-TechAssets뿐이라 StudioProjects 원본과 Library/Application Support의 v1.2 검색 프로그램은 해당 백업에 포함되지 않음.
다른 코드 파일을 백업하려면 보안키·개인정보 제거 검토, 개별 승인, 암호화 보관/복원시험 필요.
장애 발생 후 중단한 로컬/NAS/Drive LaunchAgent 예약은 여전히 disabled이며, 본 작업에서 재개하지 않음.
GitHub 저장소 추가 commit/push 없음. 원본 소스코드 변경 없음.
