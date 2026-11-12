# 120. Google Drive File Provider · 자동 업로드 권한 해결 및 실증 v1.0
실사일: 2026-11-03 KST
대상: Mac Studio / yongho 사용자의 ROUTABL 기술자산 AES-256 백업
상태: 실제 Google Drive 파일 신규 업로드 검증 완료, 무인 정기 실행은 다음 예약 시각 전이라 미검증

## 1. Finder 상태
사용자 제공 화면에서 Google Drive 연결, '내 드라이브', '다른 컴퓨터', ROUTABL-TechAssets-Backup 폴더 및 기존 ZIP 표시.
'사용 설정(Enable)' 버튼은 없었으며 추가 로그인/전체 Drive 미러링은 필요 없음.
Finder에서 Drive 폴더를 연 뒤 원격 터미널도 내 드라이브 34개 항목과 백업 폴더의 파일명/크기 열람 성공.
기존 온라인 ZIP 내용 읽기는 macOS File Provider errno 11로 차단; 기존 파일의 바이트를 직접 읽지 않도록 스크립트 수정.

## 2. 신규 파일 쓰기·Google Drive 서버 검증
시험 메모: ROUTABL_UPLOAD_PROBE_20261103_0808.txt (92바이트)
Mac Finder Drive 경로에 직접 생성 후 Google Drive 서버에서 독립 조회 성공.
Drive 파일 ID: 1RUOUw6yAECH3e25MTE0-SwpPmEmFq6j1
검증용 암호화 백업 ZIP 복사(기존 원본 보존, 이름 충돌 방지):
ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST_AUTO_VALIDATION.zip
서버 파일 ID: 1w5eMFY88nvGGkjlqErN-EYjGg5F4pkPo
Mac 새 파일 생성 → Drive 서버 확인 → Drive 원본 다시 다운로드 → SHA-256 확인.
크기 69,725,994바이트 / SHA-256
45bd23b30cbc84fb0e156e8a1e878a22e84dae13e8659c8616167e355c6d5389
ZIP CRC 검사 정상; ZIP 멤버 17개.
기존 수동 업로드본 파일 ID 1vYCFVE1FAHhoeER0iABtXMypmmgXQ2G9 역시 동일 SHA.
중복 검증본과 92B 시험 파일을 Drive에 남겨 두었으며 삭제·덮어쓰기 미실시.

## 3. macOS LaunchAgent 백그라운드 TCC 제한 우회가 아닌 정상 앱 실행 경로
launchd가 직접 실행한 python3은 외장 SSD의 Info.plist 및 NAS 자료를 읽을 때 Operation not permitted 발생.
등록 작업에서 Terminal 앱으로 .command 파일을 열면 사용자의 기존 승인된 파일 접근 경로 사용 가능.
시험 1: launchctl 제출 job이 Terminal에서 테스트 스크립트 실행, SSD readable true · Drive folder list true.
시험 2: /usr/bin/open -gj -a Terminal <.command>를 launchctl 제출 작업으로 실행. GUI 앞으로 끌어오지 않고 SSD/Drive 접근 모두 성공.
시험용 일시 제출 job(com.routabl.assetbackup.tccprobe / hiddenprobe)은 제거함.
Python 전체 디스크 접근 권한 부여, File Provider DB 재설정, OS 권한 무분별한 확대는 하지 않음.

## 4. 세 정기 예약 설정
04:30: com.routabl.assetbackup.daily
       RUN_ROUTABL_LocalScheduledBackup.command
       기존 ROUTABL_ScheduledBackup_v1_0.py (백업 본체 변경 없음)
05:00: com.routabl.assetbackup.nas.daily
       RUN_ROUTABL_NASScheduledBackup.command
       기존 ROUTABL_NASReplication_v1_0.py (NAS 복제 본체 변경 없음)
05:20 + 06:00: com.routabl.assetbackup.drive.daily
       RUN_ROUTABL_DriveUpload_v1_2.command
       신규 ROUTABL_DriveUpload_v1_2.py (v1.1 보존)
세 LaunchAgent 모두 GUI 도메인 gui/501에 bootstrap, plutil 유효성 확인, launchctl kickstart 시험 종료 코드 0.
Drive 시험 후 last_drive_result.json: PROVIDER_EXISTING_SIZE_MATCH_REMOTE_HASH_PENDING, 같은날 스냅샷, 기존 ZIP 크기 동일.
기존 Drive 온라인 ZIP 내용이 로컬에 다운로드되어 있지 않으므로 Script는 이름+크기만 판단, 클라우드 SHA 성공이라 거짓 보고하지 않음.
새 ZIP은 온라인 파일과 구별되는 이름으로 한 번만 생성하며 기존 파일 덮어쓰기 없음.
Mac의 사용자 로그인/Terminal/Drive 데스크톱 실행, 외장 SSD·NAS 연결이 필요.
로그인하지 않았거나 잠든 상태의 예약 실행 성공은 현재 미검증.

## 5. 실제 무인 예약 실행은 내일 검증해야 함
2026-11-04 04:30 / 05:00 / 05:20 / 06:00 예약.
각 log last_result.json / last_nas_result.json / last_drive_result.json의 날짜와 스냅샷 경로 대조.
Drive 서버에서 2026-11-04 이름의 새로운 ZIP을 확인하고 실제 다운로드 SHA-256 일치 확인 후에만 '완료' 판정.
launchctl의 종료 코드 0은 Terminal 작업 시작 성공일 뿐 백업 본체의 성공을 의미하지 않음.

## 6. 범위 및 보안
기존 Firebase, GitHub, 배포 APK, NAS 봉인본, AES 이미지 데이터 삭제/수정 없음.
시험 파일과 검증용 새 ZIP만 Drive에 추가.
기존 비밀번호, 인증 토큰, Admin SDK JSON 등은 스크립트/감사문서에 저장하지 않음.
현재 AES-256 이미지 /Volumes/ROUTABL-Secure은 마운트 해제 상태.
새 기술자산 관리 스크립트·감사문서는 다음 성공한 로컬 백업 시 포함됨.
