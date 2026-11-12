# 120. ROUTABL 암호화 백업 일일 예약 — 설치 및 실증
기준 시각: 2026-11-03 07:xx KST
실행 Mac: MacStudioui-MacStudio.local / macOS 로그인 계정 yongho(uid 501)
방식: 사용자 GUI LaunchAgent (시스템 전체 LaunchDaemon 아님).

## 설치된 예약
Label: com.routabl.assetbackup.daily
설정 파일: ~/Library/LaunchAgents/com.routabl.assetbackup.daily.plist
원본 보관: ~/ROUTABL-TechAssets/00_GUIDE/com.routabl.assetbackup.daily.plist
실행: /usr/bin/python3 ~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_ScheduledBackup_v1_0.py
StartCalendarInterval: 매일 04:30 (Mac 로컬 시간 Asia/Seoul)
RunAtLoad: false / Umask: 0077 / ProcessType: Background
로그: ~/Library/Logs/ROUTABL-AssetBackup (폴더 700, 로그·상태 파일 600).
기존 백업 본체: 00_GUIDE/ROUTABL_SecureBackup_v1_0.py (변경하지 않음).
새 wrapper: 실행 잠금, 같은 날 성공시 중복 방지, 성공·오류 상태 파일, 600초 이상 실행시 시간 초과 및 마운트 확인.

## 이번 회차 검증
- Mac 현재 사용자와 SSD 암호화 상태 재확인, 이미지 AES-256 유지.
- 사용자 직접 테스트: 2026-11-03 07:05 KST 실행, 파일 28개, SHA-256 전체 대조, 자동 분리 성공.
- 재실행: SKIPPED_ALREADY_SUCCEEDED_TODAY (당일 성공에 대한 중복 방지 확인).
- launchctl bootstrap gui/501 성공, launchctl print에서 Hour 4, Minute 30, calendar interval 감시 확인.
- launchctl kickstart 시험: stdout에 당일 중복 생략 기록, last exit code 0.
- 암호화 볼륨 /Volumes/ROUTABL-Secure는 시험 후 미마운트(잠긴 상태).

## 주의할 점
- 아직 2026-11-04 오전 04:30 예정 시간에 실제로 실행된 기록은 없다. 성공으로 판정하지 않는다.
- Mac 로그인 전에는 사용자 LaunchAgent가 동작하지 않을 수 있음. 잠든 상태라면 깨울 때 실행될 수 있지만 종료·로그아웃 상태의 보장은 없음.
- 외장 SSD 미연결, 키체인 잠김, 계정 변경 시 실패하며 원본이나 이전 백업을 수정하지 않음.
- 실패 시 Mac 내부 last_result.json과 launchd 로그에 기록. ChatGPT 알림·메일 통지는 아직 미설정.
- 자동 정리/삭제·보존 기간 기반 삭제 없음. 수동으로 지우지 말고 저장 용량 모니터링 후 정책 결정.
- NAS·Google Drive 원격 복제 미설정. 암호화 이미지 자체의 이중 원격 보관과 독립 복원 시험은 향후 단계.
- 키체인과 별도로 사용자가 암호 복구수단을 안전하게 보관해야 함. ChatGPT에 암호 공유하지 않는다.
- 운영 Firebase/GitHub/NAS 원본 및 기존 ASSET-SEARCH v1.1 미변경.

## 등록·해제 방법(향후 유지보수)
등록 확인: launchctl print gui/501/com.routabl.assetbackup.daily
실행 결과: cat ~/Library/Logs/ROUTABL-AssetBackup/last_result.json
작업을 종료하려면 먼저 사용자 승인 후 LaunchAgent bootout/파일 제거를 수행한다.
