# 120. 라우터블 기술자산 Mac Studio → Synology NAS 통합백업 최종 검증

작성: 2026-11-04 KST  
종합 판정: **수동 통합 AES-256 백업·NAS 실증 증분 저장·암호화 이미지 재조립 PASS / 무인 예약 운영과 NAS 복호화 내부 전체 복원은 별도 공동 검증 필요.**

## 1. 운영 범위 확정

Mac Studio → AES-256 암호화 백업 이미지(외장 SSD) → NAS 내용 기반 증분 보관.
Google Drive는 ChatGPT 관리 범위에서 제외함. 사용자가 NAS Cloud Sync로 주 1회 최종 오프사이트 보관을 관리한다.
기존 Google Drive 자동 백업 launchd 작업은 disabled이며 ChatGPT의 '라우터블 Drive 무인 업로드 첫 검증' 예약도 비활성화함.

## 2. 최신 실제 백업 성공 기록

| 항목 | 결과 |
|---|---|
| 기준 자산대장 | `asset_manifest_v0.13.json` |
| 등록 자산 | **73개**, 파일별 SHA-256 모두 일치 |
| 등록 자산대장 SHA-256 | `7e31a60be05b8528292433bd44cdad10d02ecae7e3f79056b437fdef9800929d` |
| 로컬 AES-256 암호화 스냅샷 | `ASSET_V21_20261104_000342_KST_26699` |
| 로컬 기술자산 파일 | **3,308개**, 소스선택 및 암호화 대상 파일 해시 검증 |
| 로컬 스냅샷 영수증 SHA-256 | `33c7ecd271617f127ffdedcd08ddd22be712b8f5db6bd4962875ada76794f698` |
| 통합 백업 최종 성공 | 2026-11-04 00:07 KST |
| NAS CAS 새로 저장한 암호화 구성파일 | **68개**, **559,083,520바이트** |
| NAS CAS 기존 파일 재사용 | **200개** |
| 최신 NAS CAS 구성 총계 | **268개** |
| NAS 증분 자료 전체 재조립 | **268개, 2,189,861,748바이트 SHA-256 일치** |
| 재조립본과 원본 AES 이미지 비교 | 전체 일치 |
| 재조립본 AES-256 구조 검증 | PASS |
| 격리 재조립 시험 폴더 | 삭제 완료 |
| 로컬 AES 마운트 상태 | 정상 종료, 잠금/마운트 해제 |

핵심 검증 영수증 (Mac Studio):
- `~/Library/Logs/ROUTABL-AssetBackup/last_selective_v21_result.json`
- `~/Library/Logs/ROUTABL-AssetBackup/last_manual_mac_nas_cas_v01.json`
- `~/Library/Logs/ROUTABL-AssetBackup/nas_cas_restore_ASSET_V21_20261104_000342_KST_26699.json`

## 3. 통합 원클릭 수동 실행 도구

- `~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_MacToNasOneShot_v0_1.py`
- `check`: 연결·보안조건 사전검사만 수행.
- `run`: 중복 실행 잠금 → 최신 자산대장과 파일 목록 해시 확인 → 로컬 AES 스냅샷 → NAS CAS 증분 저장 → 최종 NAS 동일 회차·SHA-256 검증.
- 실제 `run` 성공 영수증 기록 확인. Google Drive 전송·Terminal GUI 자동 실행·예약 등록·기존 스냅샷 삭제 없음.
- 증분 CAS 기반: `00_GUIDE/ROUTABL_NAS_ContentAwareBackup_v0_2.py`
- 별도 이미지 재조립 QA: `00_GUIDE/ROUTABL_NAS_CAS_EncryptedImageRestoreQA_v0_1.py`

## 4. 감사자료의 변동 원본 문제 해결

- 과거 v0.12 자산대장의 64개 레코드 가운데, 백업 수행 후 갱신된 `last_selective_v21_result.json`의 현재 SHA-256이 과거 기록과 달라짐.
- 실행 결과처럼 계속 변화하는 백업 로그 5건은 기술자산 v0.13에서 **변경 불가능한 파일 사본으로 분리**:
  `~/ROUTABL-TechAssets/60_AUDIT/IMMUTABLE_RECEIPTS_20261103/`.
- 이전 레코드의 원본 경로, 이전 SHA-256, 당시 바이트 수, 새로운 사본 SHA-256을 신규 레코드에 기록함.
- v0.12 자산대장은 수정하지 않았으며 원래 로그도 수정하지 않음.
- v0.13 활성 레코드 73개 파일의 크기·SHA-256 전수 검사 통과.
- v0.13 등록 뒤 생성한 본 최종 보고서와 최신 성공 영수증은 **다음 백업 회차에 반영할 신규 자료**이다. 마감 보고서를 쓰고 다시 백업하는 무한 반복을 피하기 위해 이번 회차의 최종 성공 영수증을 판정 근거로 둔다.

## 5. macOS GUI 진단 앱

- 신규 설치(기존 검색앱과 무관): `~/Applications/라우터블 기술자산 백업 진단 v0.1.app`
- Swift/AppKit 네이티브 앱이며 ad-hoc 코드 서명·패키지 구조 검증 통과.
- Swift 13단계 파일 접근 진단은 Mac 사용자 실행 환경에서 PASS, 가상 EACCES는 최초 실패에서 중단.
- 앱은 읽기 전용 진단과 macOS 백그라운드 설정 열기만 제공. 자동 백업·자동 예약 설치는 수행하지 않음.
- 배포 보관 ZIP: `~/ROUTABL-TechAssets/70_EXPORTS/ROUTABL_Backup_Diagnostic_v0.1_20261103.zip`.
- 실제 `launchd` 무인 프로세스 권한이 확보됐다는 뜻은 **아님**. TCC 원인은 아직 확정하지 못함.

## 6. 공동 해결 목록 — 안전과 승인 관문

### A. macOS 무인 실행
- **원인/증거:** 기존 `launchctl submit` 일회성 Python이 약 10초 간격으로 6회 `PermissionError` 실패. 서비스 제거 확인.
- **현재:** 기존 로컬/NAS/Drive 예약 3개 disabled, 새로운 후보 LaunchAgent 2개 미설치.
- **사용자와 함께:** 설치된 백업 진단 앱의 13단계 버튼을 실제 GUI에서 누르고 표시 내용을 확인. 그 결과를 기준으로 서명된 전용 헬퍼/ServiceManagement 경로와 최소 권한을 정리해 승인받는다.
- **금지:** 불명확한 원인에 대해 전체 디스크 접근을 무차별 허용하거나 과거 재시작 방식 재사용 금지.

### B. NAS 복호화 후 내부 기술자산 전체 복원
- NAS CAS → AES-256 이미지 268개 구성파일 전체 재조립은 이미 검증됨.
- 그 이미지를 사용자 Keychain/암호로 **읽기 전용 마운트하고 내부 3,308개 파일의 SHA-256을 직접 검사**하는 시험은 원격 실행 정책 제한 때문에 미완료.
- 사용자의 Mac GUI 승인 환경에서 실시하고 암호/키는 절대 채팅 또는 감사파일로 공유·기록하지 않는다.

### C. 검색 v1.5 마지막 UI 확인
- 원본 검색/정식 파일 우선/Finder 위치 표시는 사용자 실기기 확인 PASS.
- '검색 목록 새로 고침' 실제 버튼 클릭 확인은 미완료. 자동 API 시험 성공과 혼동하지 않는다.

### D. 별도 운영: NAS Cloud Sync
- NAS → Google Drive 주 1회 외부 보관은 사용자가 Synology에서 관리.
- 가능하면 **완료된 고정 암호화 스냅샷만** Cloud Sync로 전송하고, 진행 중인 Time Machine 이미지 파일의 실시간 복제를 완전한 복원 백업으로 오인하지 않는다.
- Cloud Sync 업로드·다운로드·무결성 검증은 이 120번 ChatGPT 실행의 완료 기준에서 제외.

## 7. 삭제 금지·보존

- NAS CAS는 기존 전체 이미지 `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`를 참조하므로 **해당 기준 백업을 삭제·이동·덮어쓰기하면 증분 체인이 깨질 수 있음**.
- CAS manifests와 blobs, AES 외장 SSD 원본, 역사적 자산대장 v0.1~v0.12 및 기술자산 등록된 파일을 임의로 삭제하지 않는다.
- NAS 보존기간/자동 정리는 기준 의존성으로 인한 안전성 검증 전까지 금지.
- GitHub·Firebase·운영 배차/고객 데이터는 변경하지 않았음.

## 8. 최종 판정

**자동 백업 운영 전체가 완료되었다고 판정하지 않는다.**
그러나 수동 통합 백업, 최신 자산대장 정합성, NAS 내용기반 실제 증분, 원본과 동일한 암호화 이미지 완전 재조립은 실데이터로 검증 완료하였다.
공동 작업 필요 항목은 위 A/B/C 3개이며, Google Drive는 사용자 NAS Cloud Sync 별도 운영으로 분리하였다.
