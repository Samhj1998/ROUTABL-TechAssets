# 120번 공동 해결 — Mac GUI 진단·검색 새로고침 검증·NAS 내부 복원 준비

작성: 2026-11-04 KST

## 1. 백업 진단 앱 사용자 화면 실기기 — 완료

- Mac Studio `~/Applications/라우터블 기술자산 백업 진단 v0.1.app`을 실제 실행.
- macOS 접근성 UI에서 `13단계 읽기 전용 진단 실행` 버튼을 실제 클릭.
- 앱 실제 상태: **읽기 전용 접근 통과 · 무인 백업 권한은 아직 별도 검증 필요**.
- 기존 13단계 CLI/Swift 직접 실행 검증을 넘어 앱 GUI 버튼까지 실증.
- `macOS 백그라운드 설정 확인` 버튼도 실제 클릭하여 System Settings의 `로그인 항목` 화면 열림 확인.
- **이는 앱의 일반 사용자 세션 접근 확인이며 독립 launchd 실행 권한 승인/실증이 아님.**
- 기존 Mac/NAS/Drive 예약 3개는 disabled 유지, 신규 백그라운드 LaunchAgent 등록·활성화 없음.

## 2. 검색 v1.5 실제 새로고침 버튼 — 완료

- Mac Studio의 `라우터블 기술자산 검색 v1.5.app`을 실행. Safari 로컬 검색 UI 표시 확인.
- macOS 접근성 UI에서 실제 **검색 목록 새로 고침** 버튼 클릭.
- Safari UI 실제 표시: **갱신 완료 · 5519개 항목**.
- 로컬 검색 서버 `127.0.0.1:8769/api/status`에서 `refresh.state=complete`, `last_error=null`, `total=5519`, `before=5519`, 갱신시간 2026-11-04 00:57:35 KST 확인.
- 따라서 기존 자동 API 시험과 구분되는 **사용자 화면을 통한 실기기 버튼 시험 완료**로 판정.

## 3. NAS 복호화 후 내부 파일 검증 — 준비 완료, 승인 대기

- 최신 NAS 암호화 기준 + 증분 CAS를 사용하여 **2,189,861,748바이트, 268개 암호화 파일**로 구성된 AES-256 sparsebundle 전체를 SSD 격리 위치로 다시 복원.
- 복원된 모든 암호화 구성 파일 SHA-256, 이미지 AES-256 구조 검증 통과.
- 복원 위치:
  `/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/RestoreVerificationV2/USER_READONLY_MOUNT_ASSET_V21_20261104_000342_KST_26699/ROUTABL-SecureBackup.sparsebundle`
- 확인용 영수증:
  같은 상위 폴더의 `READONLY_RESTORE_STAGING_RECEIPT.json`.
- **이미지는 현재 마운트하지 않았고 암호/Keychain 접근도 시도하지 않음.**
- 안전 검증 프로그램 `00_GUIDE/ROUTABL_NAS_UserMountedReadonlyVerify_v0_1.py` 작성·문법 검사 완료.
  - **사용자 작업으로 원본 NAS가 아닌 SSD의 복원 이미지**를 읽기 전용으로 마운트한 경우에만 작동.
  - hdiutil이 표시한 실제 마운트 출처가 정확히 해당 복원 이미지인지 확인.
  - 파일 시스템 읽기 전용 플래그 확인.
  - 이미지 내부 `snapshot_receipt.json`의 SHA-256와 실제 로컬 백업 영수증 연결 확인.
  - 3,308개 내부 파일 모두 SHA-256 전수 검사 후 성공 영수증 기록.
  - 파일을 일반 폴더로 추출·복사하지 않음.
  - 검증기는 이미지 마운트·분리·암호 조회·비밀번호 기록·macOS 접근권한 변경을 **전혀 수행하지 않음**.
- 마운트되지 않은 상태에서는 검증기가 안전하게 `BLOCKED_OR_FAILED_SAFE` 판정; 완료 주장 금지.
- Mac 사용자에게 **읽기 전용 마운트와 필요한 Keychain GUI 승인**을 요청한 뒤 검증을 재개해야 함.
- 복원 이미지 원본 AES-256 파일(운영 SSD) 및 NAS 보관 원본은 변경하지 않았음.
- 검증 후 사용자가 마운트 해제한 사실 확인 뒤 SSD 격리 시험본을 정리하는 후속 단계 필요.

## 4. 남은 공동 해결 과제

1. **NAS 내부 3,308개 실제 복호화 읽기 검증**: 사용자 Mac에서 읽기 전용 마운트 승인 후 시행.
2. **macOS 독립 백그라운드 권한/무인 자동화**: GUI 진단 13단계 통과와 별개로 실패 원인 미확정. 필요시 Apple SMAppService 기반 전용 헬퍼를 설계하고 사용자의 명시적 승인 이후 한 번만 실행하여 검증. 기존 `launchctl submit` 재시도 금지.
3. Google Drive는 사용자 Synology Cloud Sync 주간 최종 오프사이트 보관, ChatGPT 범위에서 제외.

## 5. 기존 자료의 안전한 보존

- 검증된 최신 수동 Mac→NAS 백업: v0.13 자산대장 73개를 포함한 3,308개 기술 파일.
- NAS CAS 기준 보관본 `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`은 모든 증분이 참조하므로 삭제·이동 금지.
- 운영 Firestore·기사앱·고객앱·GitHub·NAS 원본·기존 예약 설정을 변경하지 않음.
- 본 보고서는 마지막 실제 검증 백업 이후 생성된 신규 감사 기록으로, 직전 백업에 이미 포함됐다고 주장하지 않음.
