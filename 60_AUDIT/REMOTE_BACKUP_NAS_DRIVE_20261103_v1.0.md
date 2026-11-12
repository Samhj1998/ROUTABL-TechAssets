# 120번 NAS·Google Drive 암호화 백업 단계 감사 v1.0
실사일: 2026-11-03 KST / 원본 백업 파일: AES-256 Sparse Bundle

## 원본 안전 확인
외장 SSD: /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle
macOS 이미지 검사: Encrypted=1, Key Size=256, 20GB 가상 공간.
복제 전후 /Volumes/ROUTABL-Secure 미마운트 확인. 기존 원본과 NAS 백서 봉인본 미수정.

## NAS 최초 복제 (실제 실행)
대상: /Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots/20261103_071431_KST
16개 파일, 총 61,232,244바이트. 소스-타깃 SHA-256 전부 일치, 원본 변동 없음.
증거 파일: NAS_ENCRYPTED_BACKUP_RECEIPT.json
증거 SHA-256: e8fd6a2a48b8d02a9c3cea44da0b15434806188f9731e86380a0716649733c20

## NAS에서 독립 파일 복구시험
NAS 첫 스냅샷을 Mac 내부 40_WORKING/NAS_INDEPENDENT_RESTORE_20261103_071431_KST에 새로 복사.
16개 구성 파일 전체 SHA-256 일치 및 복원 사본 AES-256 이미지 메타데이터 확인.
실제 복원본을 마운트하여 내부 자산을 읽으려는 원격 작업은 보안 실행 제한으로 차단됨.
따라서 실제 암호 해제·내부 파일 읽기/분리까지의 종단간 복원검증 완료는 아님.
원격 제한을 우회하지 않았음. 디스크 이미지 원본과 복원 사본은 그대로 보존.

## NAS 자동 복제 등록
추가 스크립트: 00_GUIDE/ROUTABL_NASReplication_v1_0.py
매일 05:00 사용자 LaunchAgent: ~/Library/LaunchAgents/com.routabl.assetbackup.nas.daily.plist
필수 조건: 같은 날 04:30 이후 로컬 백업 성공 기록 + 이미지 잠금 상태 + NAS 온라인 + AES-256 유지.
소스 이미지 크기 2GB 상한, 원본 재해시, 대상 해시 일치, 중복 실행/중복 성공 방지, 기존 백업 자동 삭제 금지.
실제 수동/프로그램 복제 성공:
 /Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots/NAS_AUTO_20261103_071957_KST
17개 파일 검증; 영수증 SHA-256 b8a08e786045adde625f969169d94269b9b610e6dff912a3814359583deefccf
launchctl bootstrap 및 kickstart 시험 정상; 이미 당일 성공하였으므로 예약 테스트는 중복 스킵, 종료 코드 0.
2026-11-04 05:00 무인 실행 기록은 아직 없음; 검증 대기.

## Google Drive 준비
기존 Backup_SmartDispatch_Data와 별도 Google Drive 루트 폴더:
 ROUTABL-TechAssets-Backup (ID 1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS)
 URL: https://drive.google.com/drive/folders/1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS
생성 후 Drive 검색으로 폴더 존재·비공유(false) 확인, fetch 결과 파일 0개.
Mac Studio에는 Google Drive for desktop 앱 및 동기화 경로가 확인되지 않음.
연결된 Drive 업로드 도구는 업로드할 connector file_uri를 요구하고 Mac 파일 경로는 받지 않음.
이에 Mac→Drive 자동 업로드를 실제 수행할 수 없으며, 성공으로 보고하지 않음.

## Drive 업로드 준비 패키지
기본 패키지(최신): /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/DriveStaging/ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST.zip
크기 69,725,994바이트, ZIP 내부 17개 파일 각각 NAS 영수증 SHA-256 일치.
패키지 자체 SHA-256:
45bd23b30cbc84fb0e156e8a1e878a22e84dae13e8659c8616167e355c6d5389
ZIP은 '암호화된 sparsebundle 데이터'를 전달하기 위한 일반 ZIP이므로 바깥쪽 이름/메타데이터는 암호화되지 않음.
패키지 내용은 비밀번호를 입력해야 열 수 있는 AES-256 sparsebundle 원본 데이터.
Drive 업로드/다운로드/원격 복원 테스트는 미완료.

## 앞으로의 관문
1. 사용자가 위 ZIP을 Drive 폴더로 한 번 직접 업로드하거나, Mac Studio에 Google Drive 데스크톱 앱 설치·로그인 승인.
2. 연결된 Drive에서 파일명·크기 확인, 파일 다운로드 후 SHA-256 원본과 대조.
3. NAS 복원본 암호 해제·내부 파일 읽기 시험은 Mac GUI의 합법적 사용자 승인 경로로 별도 수행.
4. 원격 백업 보존기간/용량정책은 향후 결정. 현재 자동 삭제 없음.

## 변경되지 않은 부분
Firestore, GitHub, 배포 APK, ASSET-SEARCH v1.1, NAS 기존 백서 봉인본, 외장 SSD 전체 파티션, 기존 백업.
