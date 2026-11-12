# 120. Google Drive 최종 무결성·복원 및 자동 업로드 검증 (2026-11-03)
작업 기준: 기존 Firestore / GitHub / NAS 봉인본 / 암호화 스냅샷 원본 덮어쓰기·삭제 없음.

## Google Drive 원격 파일 회수 / 비트 단위 복원 검사 — 성공
Drive 파일 ID: 1vYCFVE1FAHhoeER0iABtXMypmmgXQ2G9
대상 폴더 ID: 1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS
파일: ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST.zip
Google Drive 원격 다운로드: 성공 (ChatGPT 연결 저장소 및 격리된 검증 컨테이너)
실제 다운로드 크기: 69,725,994 bytes
실제 다운로드 SHA-256: 45bd23b30cbc84fb0e156e8a1e878a22e84dae13e8659c8616167e355c6d5389
기존 업로드 준비본 SHA-256과 완전히 일치.
ZIP 내부: 17개 파일 모두 압축 CRC 검사 통과, 읽기/해시 계산 가능.
Drive 서버 메타데이터의 크기 및 비공유 상태 확인.
중요: ZIP은 암호화된 sparsebundle 데이터의 컨테이너이지만 ZIP 메타데이터 자체는 비암호화.

## 암호화 보관본 내부 접근 검증 — NAS 복원 사본 성공
NAS 첫 스냅샷을 Mac 40_WORKING/NAS_INDEPENDENT_RESTORE_20261103_071431_KST에 따로 복제한 시험 이미지:
  ROUTABL-SecureBackup.sparsebundle
AES-256 disk image 메타데이터 대조 완료.
Mac Studio에서 복원 사본을 실제 read-only 마운트 성공.
사본 안의 asset_manifest_v0.3.json 총 5개(서로 다른 백업 시점) 읽기 성공.
5개 모두 현재 Mac 원본과 SHA-256 일치.
시험 후 복원 볼륨 강제 추출 없이 정상 언마운트.
판정: NAS 복원 사본의 실제 암호 해제·내부 파일 열람 성공.
한계: Google Drive에서 내려받은 ZIP 자체를 Mac에서 직접 추출 후 마운트한 시험은 미실시.
두 저장본의 동일성은 Drive 다운로드 ZIP의 SHA-256이 사전 검증본과 일치하는 것으로 확인.

## 자동 업로드 — 설치만 완료, 실제 클라우드 전송 미완료
파일: ~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_DriveUpload_v1_1.py
예약: ~/Library/LaunchAgents/com.routabl.assetbackup.drive.daily.plist
이름: com.routabl.assetbackup.drive.daily
예정: 매일 05:20, 실패 시 06:00 재시도. 기존 로컬 04:30 및 NAS 05:00 예약은 그대로.
의존 조건: 당일 NAS SUCCESS 기록, 잠긴 외장 AES 이미지의 파일/해시 확인, 덮어쓰기 금지.
실측: 대화형 터미널 실행에서 NAS 성공 스냅샷 17개 항목을 읽고 ZIP 구성 해시 확인 성공.
스테이징 ZIP: /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/DriveUploadOutbox/ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST.zip
크기 69,725,994 bytes / SHA-256 45bd23b30cbc84fb0e156e8a1e878a22e84dae13e8659c8616167e355c6d5389
Google Drive File Provider: '내 드라이브' 폴더 열람 시 errno 11 Resource deadlock avoided.
macOS LaunchAgent에서 외장 SSD 접근: Operation not permitted (Info.plist 파일 포함). 일반 사용자 터미널에서는 접근 정상.
따라서 실제 무인 클라우드 업로드 성공/장치 권한 설정 완료로 보고하지 않는다.
권한 문제 해결을 우회하기 위해 인증키 추출/DriveFS 캐시 삭제/계정 리셋/보안 설정 임의변경 하지 않음.
Drive 업로드 상태 경로: ~/Library/Logs/ROUTABL-AssetBackup/last_drive_result.json (FAILED 기록).
백업 기존 원본 보존 및 새 예약 작업은 fail-closed.

## 사용자 확인이 필요한 Mac GUI 관문
1. Finder의 '위치' 아래 Google Drive를 클릭 후 '사용 설정(Enable)' 표시 시 승인.
2. 시스템 설정 → 개인정보 보호 및 보안 → 파일 및 폴더(또는 전체 디스크 접근 권한)에서 Google Drive 및 예약 실행 주체의 외장 볼륨 접근 상태 확인.
3. 외장 볼륨 접근을 위해 모든 앱의 전체 디스크 접근 권한을 무분별하게 부여하지 말 것.
4. 승인 후 출처/대상 파일 접근 재시험, Google Drive 서버 실제 새 ZIP 업로드·다운로드 해시 재검증을 수행해야 무인 백업 완료 판정.

## 보호된 기존 기능
매일 04:30 로컬 LaunchAgent와 05:00 NAS LaunchAgent 기존 설정은 유지.
내일 첫 실제 무인 실행의 성공 여부는 별도 예약 점검에서 확인해야 함.
Google 계정 OAuth 토큰, 서비스계정 키, 비밀번호는 코드나 보고서에 포함하지 않음.
