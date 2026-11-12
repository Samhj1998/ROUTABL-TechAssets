# 120번 라우터블 기술자산 — Mac→NAS 백업 통합 검증 및 공동 해결 목록

기준: 2026-11-03 KST
문서 성격: **통합 백업 전 검증 기록.** 마지막 실행 성공 여부는 별도 최신 영수증으로 확인한다.

## 1. 확정된 운영 범위
- **ChatGPT 담당:** Mac Studio의 기술자산 자산대장·검색·AES-256 로컬 스냅샷·Synology NAS 암호화 증분 복제 및 복원 검증.
- **Google Drive:** ChatGPT 직접 업로드·다운로드·원격 해시검증 작업 **범위에서 제외**. 사용자가 Synology의 Cloud Sync로 주 1회 최종 외부 보관 예정.
- 이전 Google Drive 관련 자동 예약 `com.routabl.assetbackup.drive.daily`는 disabled이며 재활성화하지 않음.
- 원본 코드·Firebase·GitHub·NAS 기존 스냅샷 삭제·덮어쓰기 없음.

## 2. 확인된 암호화 로컬 및 NAS 증분 백업
- 실제 로컬 AES-256 백업: `ASSET_V21_20261103_232836_KST_26015`
- 자산대장 기준: `asset_manifest_v0.12.json`, 등록 **64개** 포함, 선택 파일 총 **3,299개**.
- 로컬 영수증: `~/Library/Logs/ROUTABL-AssetBackup/last_selective_v21_result.json`.
- 로컬 영수증 SHA-256: `83b94ca9f313c4149bfef5d367bff50fd4f5ef37518b3beec52618dc50cba015`
- NAS 내용기반 CAS 기준 전체 이미지: `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639` (변경·이동·삭제 금지).
- 실환경 NAS 증분 저장 결과: 암호화 파일 **67개(547,971,072바이트) 신규**, 기존 기준 **138개 재사용**.
- 최신 CAS 매니페스트: `CAS_ASSET_V21_20261103_232836_KST_26015.json` (총 205개 항목).
- NAS 기준 + 증분을 SSD 격리 폴더에서 재조립하여 암호화 파일 **205개, 합계 1,658,655,604바이트** 전부 SHA-256 일치 확인.
- 재조립 이미지의 구조가 AES-256임을 확인했고, 기존 Mac 암호화 이미지와 해시 비교 통과.
- 재조립 시험 폴더 삭제 확인. 이는 암호화 이미지 재구성 검증으로, **NAS 복호화 후 내부 파일 전체 복원**까지 입증하지는 않음.

## 3. 동작하도록 새로 준비된 운영 보조 도구
- `00_GUIDE/ROUTABL_NAS_ContentAwareBackup_v0_2.py` — NAS SMB 호환 파일 확정 방식, 실제 변경된 구성파일만 보관.
- `00_GUIDE/ROUTABL_NAS_CAS_EncryptedImageRestoreQA_v0_1.py` — NAS 구성 요소를 격리 SSD에 재조립·SHA-256·AES-256 구조 비교하고 임시 사본 정리.
- `00_GUIDE/ROUTABL_MacToNasOneShot_v0_1.py` — **한 번의 수동 실행으로 로컬 AES 백업 → NAS CAS 복제 → 동일 영수증/구성 파일 검증**. Google Drive 전송·예약 등록·원본 삭제 없음.
- macOS 진단 앱: `~/Applications/라우터블 기술자산 백업 진단 v0.1.app`.
  - Swift/AppKit 네이티브 앱, 임시 작업 폴더의 동일 앱을 ad-hoc 서명·코드 검증 후 사용자 Applications에 별도 신규 설치(미실행).
  - Swift 진단 실행 파일은 수동 사용자 환경 13단계 통과, 권한 거부 가상 시험은 최초 EACCES에서 즉시 중단.
  - Apple 개발자 계정 서명·공증된 배포가 아니며, 이것만으로 macOS 독립 백그라운드 서비스 권한이 해결된 것은 아님.
- 위 도구 중 이번 통합 자산대장 기준 이후 작성된 파일의 백업 여부는 **다음 한 번의 수동 백업 성공 영수증에서 별도 검증**.

## 4. macOS 무인 실행 안전 관문 — 공동 해결 필요
- 기존 `launchctl submit` 방식은 6회 반복 실패 및 `PermissionError` 발생, 서비스 제거 확인. **다시 사용하지 않음**.
- 기존 `com.routabl.assetbackup.daily`, `com.routabl.assetbackup.nas.daily`, `com.routabl.assetbackup.drive.daily` 모두 disabled.
- 신규 v2.1 plist는 초안만 있으며 설치하지 않음.
- 사용자와 함께 macOS 설정을 열고 **정확한 앱 실행 주체의 외장 SSD/NAS 접근 권한** 확인.
- 별도 ServiceManagement/SMAppService 기반 서명된 전용 helper는 설계 방향만 확정, 현재 미구현/미등록.
- macOS 권한을 임의로 낮추거나 전체 디스크 접근을 일괄 부여하지 않음.

## 5. 남는 공동 해결 및 사용자 확인 목록
1. **자동 예약 활성화 전:** macOS 배경 실행 프로세스의 권한·재시도 방지 상태 실제 검증 (사용자 macOS 앱 승인 필요).
2. **NAS 내부 복원:** NAS의 복원 암호화 이미지를 사용자 Keychain으로 **읽기 전용 마운트**하고 암호화 컨테이너 내부 자산 전체 해시 검사 (원격 안전 제한으로 미검증). 암호를 ChatGPT에 제공하지 않음.
3. **검색 v1.5:** 검색 화면의 '검색 목록 새로 고침' 버튼 실제 UI 클릭 및 결과 확인 (API/자동 시험은 별도 통과).
4. **Cloud Sync 주간 외부 보관:** Synology NAS에서 사용자가 별도 설정·관리. ChatGPT의 백업 범위에서 제외.

## 6. 보존·보안 주의
- NAS CAS 기준 전체 이미지 `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`는 새 CAS 매니페스트가 참조하므로 **삭제·이동·덮어쓰기 금지**.
- NAS CAS 정리는 참조 의존성을 검증한 후에만 별도 설계; 자동 prune 없음.
- 인증서·패스키·Firebase Admin SDK JSON·비밀번호를 새로운 실행파일·감사기록에 저장하지 않음.
- 기존 여러 백업 프로그램과 자산대장 원본을 그대로 남기며 신규 버전을 독립 생성.
- 최신 수동 실행의 성공·실패, NAS 해시 검증 결과는 실제 최종 영수증을 최우선 근거로 판단한다.
