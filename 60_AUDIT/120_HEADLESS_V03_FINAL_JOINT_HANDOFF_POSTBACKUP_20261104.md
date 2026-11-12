# 120번 라우터블 Mac→NAS 자동 백업 안정화 — v0.3 최종 인수인계

작성: 2026-11-04 KST
판정: **백업·NAS 증분 보존·AES-256 복원 검증 PASS, 실제 무인 운영 승인은 미완료.**

## 1. 최종 완료 상태

- 가장 최근 수동 통합 성공: `2026-11-04 02:23:17 KST`.
- 등록 자산대장: `asset_manifest_v0.14.json`, **81개** 항목, 활성 SHA-256 **81/81 PASS**.
- 자산대장 SHA-256: `f2e7d88d16b6b2aa98d8cc53ed6cbf099f8b19bc4c7cbce072b1ee62ffd7233d`.
- AES-256 최신 스냅샷: `ASSET_V21_20261104_021823_KST_29291`.
- 저장한 기술자산 파일: **3,324개**.
- 로컬 스냅샷 영수증 SHA-256: `49195d21fb480b25710c8f8542885deb54a77799f2a985ff59126564d9e79478`.
- NAS CAS 기준본+증분: 암호화 파일 **331개**, 신규 **67개/553,717,760바이트**, 이전 데이터 **264개** 재사용.
- NAS CAS 독립 복원: **331개/2,721,366,900바이트**, 각 SHA-256 전부 일치, Mac 최신 암호화 이미지와 전체 일치.
- 복원된 이미지 AES-256 구조 PASS. 복원 QA 임시 파일은 정리. 복호화 불필요한 암호화 이미지 수준 검증임.
- 별도의 과거 v0.13 복원에서는 내부 파일 3,308개를 **실제로 복호화한 읽기 전용 이미지에서 전수 SHA-256 PASS**.
- SSD2TB·NAS 연결 정상, 암호화 디스크 마운트 해제 확인, 상태검사 `HEALTHY_EVIDENCE`.
- 운영 중 실제 백업·NAS CAS 기준본·Firebase·GitHub·Android 소스에 손상/삭제/덮어쓰기 변경 없음.

## 2. 이번에 보완한 자동화 자산

- `~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_2.py`: 무인 실행 승인 파일을 **NAS 접근보다 먼저 확인**하고, 미승인 시 네트워크 TCC 프롬프트를 유발하지 않음.
- `~/ROUTABL-TechAssets/40_WORKING/HEADLESS_NATIVE_V0_3/ROUTABLBackupAgent.swift`: Swift 네이티브 실행, 최초 로컬 승인 검사, 20초 제한 네트워크 사전진단, 실제 복제의 별도 제한시간, 종료 상태와 현재 회차 성공 영수증 검증, JSON 상태 로그.
- `~/ROUTABL-TechAssets/40_WORKING/HEADLESS_NATIVE_V0_3/ROUTABLBackupManager.swift`: SMAppService 등록·해제·상태 GUI. 네트워크/외장 저장장치 용도 설명 키 포함.
- 설치 앱: `~/Applications/라우터블 백업 권한·안전관리 v0.3.app`. **설치 완료/코드서명 검증 PASS**.
- 배포 ZIP: `~/ROUTABL-TechAssets/70_EXPORTS/ROUTABL_BackupSafeManager_v0.3_20261104.zip` (SHA-256 `bcec8e87a8fafdefd4f88070bac26d42bd23b08118e1719f5f85b913d44cfb1a`).
- `~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_BackupApprovalGate_v0_1.py`: 명시적 사용자 입력 없이는 자동 백업 승인파일 생성 불가. `review` PASS, `approve` **미실행**.
- v0.3 로컬 진단 실제 앱 GUI PASS, Swift watchdog timeout 격리 실험 PASS, 출처 보존 및 해시 검증 PASS.

## 3. 현재 시스템 안전 상태

- 기존 세 예약 `com.routabl.assetbackup.daily`, `.nas.daily`, `.drive.daily`: **disabled**.
- 시험 도중 대기되었던 `com.routabl.assetbackup.native.v02`: **disabled**, 네이티브/Python 자식 프로세스 종료 확인.
- v0.3 서비스 `com.routabl.assetbackup.native.safe`: **아직 macOS에 등록하지 않음** (launchctl “Could not find service”). 예약 스케줄 설정은 앱에 포함되나 비활성화.
- 운영 자동 백업 승인 파일 `~/Library/Application Support/ROUTABL-AssetBackup/approval_v01.json`: **없음**.
- 사용자 OS 권한창을 자동 클릭하거나 TCC.db를 수정한 적 없음.
- Google Drive는 범위에서 제외. NAS Cloud Sync 주 1회 오프사이트 보관은 사용자 별도 관리.
- v0.3 앱은 ad-hoc 서명됨; 시스템에 Apple 코드 서명용 Developer ID 인증서 **0 valid identities**, 따라서 재서명 후 TCC 권한 유지 보장은 아직 하지 못함.

## 4. 함께 처리할 항목만

### 1) v0.3 최초 백그라운드 등록·NAS/SSD 권한
- Mac Studio 사용자 GUI에서 **`라우터블 백업 권한·안전관리 v0.3`**의 `안전 에이전트 등록`을 확인 후 클릭.
- macOS 파일 및 폴더 접근 권한은 **정확한 앱과 네트워크 볼륨/외장 SSD**에 대해 사용자 최초 승인. 승인 버튼을 자동 클릭하지 않는다.
- 승인 파일이 아직 없으므로, 등록만으로는 새 앱이 NAS에 접근하거나 실제 백업을 시작하지 않도록 설계됨.
- 등록 뒤 `SMAppService.status`, `launchctl` 등록·실행·종료, `last_native_launchagent_v03.json`의 `DISARMED_NO_APPROVAL` 증거 확인.
- 앱 코드를 변경하면 사용자 승인/번들 서명 재검증이 필요.

### 2) 운영용 서명/권한 유지 확인
- Developer ID 인증서 미설치 상태. 시험용 ad-hoc 앱은 동일 바이너리 유지 시 사용 가능할 수 있으나, **앱 재빌드·재서명 이후 권한 유지까지 보증할 수 없음**.
- 최초 권한 승인 후 로그아웃·재부팅, NAS 자동 연결·Keychain 비대화형 잠금 해제의 성공 여부를 실증. macOS 전체 디스크 접근 무조건 허용 금지.

### 3) 실제 무인 백업 활성화와 연속 운영
- 최초 TCC 승인과 v0.3 무인 단발 시험 성공을 확인한 후에만 `ROUTABL_BackupApprovalGate_v0_1.py approve`를 사용자 터미널에서 실행.
- 실질적인 AES-256 로컬→NAS CAS 백업이 예약 시각 04:30에 실행되고 성공 영수증이 갱신되는지 확인.
- **7일 연속 운영**에서 예약 누락·NAS 재연결·중복 실행·정상 잠금 해제·새로운 권한 팝업 없음·성공/실패 기록을 검증.
- 자동 실패 알림 채널(예: ChatGPT 예약 점검 또는 macOS 사용자 알림) 합의와 설치는 아직 완료하지 않음.

## 5. 주의사항
- NAS CAS 기준 보관 `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`과 `ROUTABL-Ciphertext-CAS-v0_1` 데이터는 참조 관계 때문에 임의 삭제·정리 불가.
- 이번 사후 보고서는 최신 v0.14 암호화 백업 생성 이후 작성되었으므로 **그 백업에 이미 포함됐다고 주장하지 않음**. 다음 정상 수동/무인 백업에 자동 수집될 예정.
- 백업 성공 기록과 자동 실행 준비 상태를 구분해야 한다. 수동 NAS 복원 완성과 무인 운영 완료는 다른 판정이다.
