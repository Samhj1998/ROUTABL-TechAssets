# 120. 라우터블 AES-256 백업 실행·검증 보고 v1.0
검사일: 2026-11-03 KST
Mac Studio 사용자 계정: yongho
기존 외장 SSD2TB 파티션·저장 데이터 미변경.

## 구성
- 외장 이미지: /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle
- 설정 크기: 20GB / UDSB Sparse Bundle / 암호화 이미지 AES-CBC 256-bit / 내부 APFS.
- hdiutil 및 diskutil image info로 Is Encrypted: 1, Key Size: 256 확인.
- 비밀번호·인증키를 프로젝트 파일/스크립트/ChatGPT에 기록하지 않음.
- Finder에서 마운트 시 사용자가 관리하는 Mac 키체인 연동을 이용한다.

## 실증 결과
1. 최초 이미지 생성 후 /Volumes/ROUTABL-Secure 마운트 확인.
2. 첫 백업: 23개 관리 폴더 파일 8,284,800바이트, 원본-사본 SHA-256 전체 일치.
3. 격리 복원시험: 자산대장 JSON과 백서 PDF 2개 파일을 Mac 40_WORKING의 RESTORE_TEST_20261103_v1에 복원·원본 해시 대조 성공.
4. 이미지 정상 추출 후 잠금 확인.
5. 실제 NUL 1바이트 빈 비밀번호 시도는 거부됨 (hdiutil attach -stdinpass return code 1).
6. 추가 비밀번호 입력 없이 이미지 재연결 성공(현재 로그인 키체인/계정 조건에 한정), 재추출 성공.
7. 자동화 스크립트 실행: AUTO_20261103_005329_KST 스냅샷 25개 SHA-256 대조 성공, 키체인 자동 마운트 및 자동 추출 성공.
8. 실행 종료 후 /Volumes/ROUTABL-Secure 마운트 해제 상태 재확인.

## 설치한 실행 파일
- 00_GUIDE/SETUP_ROUTABL_SecureBackup.command: 최초 설치 전용. 다시 실행하지 않는다.
- 00_GUIDE/ROUTABL_SecureBackup_v1_0.py: 기존 원본을 변경하지 않고 읽기·해시 검증 후 새 스냅샷으로만 복사한다.
- 00_GUIDE/RUN_ROUTABL_SecureBackup.command: Finder 더블클릭으로 1회 백업 가능.
- 기본 백업 원본: 00_GUIDE, 20_ORIGINALS, 30_REGISTRY, 50_VERIFIED, 60_AUDIT, 70_EXPORTS.
- 10_INBOX/40_WORKING/원본 Firebase·전 라이브러리·기타 StudioProjects는 미포함.
- 스냅샷 이름에 KST 시각 사용, 기존 스냅샷은 덮어쓰지 않음.
- 파일당 100MB, 총 1GB 넘으면 자동 진행 중단하고 범위 확인.
- 복제 시 SHA-256 불일치 또는 원본 변경 감지 시 실패 보고, 불완전 스냅샷을 자동 삭제하지 않음.

## 현재 상태와 한계
- 기존 비암호화 SSD 메타데이터 snapshots/ 및 restore-tests/ 폴더는 아직 유지. 암호화 이전 사본을 임의 삭제하지 않음.
- 새 암호화 이미지는 외장 SSD 분실·도난 대비 수단이나, Mac 로그인 계정 탈취 또는 키체인 접근 권한 악용까지 차단하지 못함.
- 키체인의 자동 마운트는 이 Mac 로그인 상태에서 실증되었으며, 재부팅·키체인 잠금·다른 사용자 세션에서는 별도 검증 필요.
- 암호 분실 시 키체인 외 별도 복구수단 확보가 필요하다. 비밀번호는 AI와 공유하지 않는다.
- 정기 실행 시각·launchd 등록은 아직 안 됨. 현재는 1회 실행형 프로그램이다.
- NAS 및 Google Drive 원격 암호화 이미지 복제·재해복구는 아직 설정/검증하지 않음.
- 운영 Firebase, GitHub, NAS 봉인본, 기존 SQLite 검색 엔진 v1.1 변경 없음.
