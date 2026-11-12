# 120번 Mac Studio → Synology NAS 자동 백업 안정화 / v0.4.2

기준: 2026-11-04 KST
**판정:** 실제 Mac→AES-256 SSD→NAS CAS 수동 통합 백업·복원 PASS. `SMAppService` 진단 전용 무인 실행 정상 종료 PASS. 네트워크 볼륨 TCC/SMB 접근 진단은 20초 제한시간으로 실패했으며 사용자 최초 승인/실환경 구분 필요. 실제 무인 암호화 백업은 미승인·미실시.

## 1. 기존 성공 베이스라인
- `asset_manifest_v0.14.json`, 등록 자산 **81개**, 최신 저장 파일 **3,324개**, SHA 검증 PASS.
- 실제 성공한 로컬→NAS 통합 백업 `ASSET_V21_20261104_021823_KST_29291`, 2026-11-04 02:23 KST.
- NAS CAS 구성 총 331개: 신규 67개, 기존 264개 재사용, 독립 AES-256 구성 파일 재조립 331개 SHA 검증 PASS.
- v0.13 백업 3,308개 파일은 이전에 실제 읽기 전용 복호화 전수 SHA 검사 PASS.
- `ROUTABL-Secure` 복원 볼륨은 마운트 해제되어 있고, SSD2TB와 NAS는 연결 유지.
- SSD/NAS 백업 기존 원본 변경·삭제 없음. Google Drive는 사용자가 Synology Cloud Sync로 주간 최종 외부 보관; ChatGPT 범위에서 제외.

## 2. 실제 SMAppService 테스트
- v0.3 `com.routabl.assetbackup.native.safe`: 등록 후 단발 진단 실행 2회, 정상 종료 0, 승인 파일 없음, NAS 접근·백업 없음.
- v0.4 테스트에서 동일한 Bundle ID/agent label을 재사용하면서 ad-hoc 코드 서명 CDHash가 변경. macOS `OS_REASON_CODESIGNING`으로 실행 거절. 유효한 정상 실행으로 보고하지 않았고 서비스 등록 해제.
- v0.4.1 새 Bundle ID 및 agent label로 macOS 정상 실행 복귀. 무승인 시험 PASS. NAS 접근 진단은 보조 프로그램 실행 위치 탐색 실패 (자식 종료 70); 진단 동의 취소, 서비스 등록 해제.
- v0.4.2 **별도 고정 식별자** `com.routabl.assetbackup.manager.v042`, agent `com.routabl.assetbackup.native.v042` 사용. Swift 실행 위치는 `Bundle.main.executableURL` 기준으로 수정.
- v0.4.2 앱 `~/Applications/라우터블 백업 권한·안전관리 v0.4.2.app` 설치, ad-hoc 서명 및 `codesign --verify --deep --strict` PASS.
- SMAppService v0.4.2 서비스 등록 결과 `enabled`, 실제 `launchd kickstart` 무승인 단발 실행 시 종료코드 **0**, 이벤트 `DISARMED_NO_APPROVAL` / `networkVolumeAccessAttempted=false` / `backupAttempted=false` PASS.
- 전용 네트워크 권한 시험을 위한 사용자 GUI 동의 파일은 `TCC_METADATA_READ_ONLY`, `backup_enabled=false`, 0600 생성 확인.
- v0.4.2 네트워크 폴더 메타데이터만 읽는 보조 프로세스는 **20초 시간 초과**. 결과 `PROBE_TIMEOUT_NO_RETRY`, 자식 코드 124, 부모 launchd 코드 13. 실제 파일 백업 및 복호화 **미실시**.
- macOS 권한 팝업 대기인지 NAS SMB 파일 접근 지연인지 아직 확정되지 않음. tccd 통합로그에서 정확한 거부/승인 원인 확정 불가.
- 해당 시험 동의는 macOS GUI에서 **취소**했고, 운영용 백업 승인 파일도 없음.
- 취소 후 v0.4.2 재실행: `DISARMED_NO_APPROVAL`, 종료코드 **0**, NAS 접근 없음, 실제 백업 없음, 대기/재시작 반복 없음.
- 구형 v0.4.1 및 v0.4 등록은 해제. v0.2와 3개 구식 정기 백업 launchd 작업은 disabled.

## 3. 예약 및 보안
- 현재 **v0.4.2 진단 전용 에이전트만 등록·활성화**: 매일 한국시간 04:30; `KeepAlive=false`, `RunAtLoad=false`.
- 실제 운용 승인 파일 `~/Library/Application Support/ROUTABL-AssetBackup/approval_v01.json` 부재 → 매일 예약 발동하더라도 실제 백업은 시작하지 않고 안전 종료.
- 진단 동의 파일 `diagnostic_consent_v01.json` 역시 제거 → 예약 시 NAS/SSD의 보호 경로에 접근하지 않음.
- 실제 자동 백업의 최초 성공은 아직 **0회**. 기록한 수동 AES→NAS 성공과 엄격히 구분.
- Mac Studio AC 전원 `pmset sleep 0` / 화면 절전 5분 확인, SSD APFS 및 NAS SMB 마운트 현재 정상. **Mac 재시작 후 NAS 자동 재연결은 미검증**.
- 현재 Apple Developer ID 코드 서명 인증서가 없음(0 valid identities), 앱은 ad-hoc 서명. 버전 교체 시 재등록·TCC 권한 유지 문제 발생 가능.
- 기존 비밀키/암호를 새 코드·앱·ZIP에 기록하지 않음. 사용자 보안 승인 팝업을 자동 클릭하지 않음.

## 4. 안전하게 보류한 공동 해결 작업
1. **NAS·SSD TCC 권한을 사용자가 Mac 앞에서 한 번 승인:** v0.4.2 관리 앱의 `NAS·SSD 접근 시험 동의 (백업 없음)`을 눌러 시험 동의를 켠 뒤, 등록된 v0.4.2 에이전트를 **단발** 실행. 나타나는 macOS 권한 요청은 사용자가 앱 이름과 대상 볼륨을 확인하고 직접 판단·승인. 무응답/타임아웃 시 동의를 즉시 취소. 이 시험은 실제 백업을 수행하면 안 됨.
2. **권한과 SMB 지연 구분:** 승인 후에도 20초 시간 초과라면 원격 기록과 macOS 네트워크 연결 상태를 확인; TCC.db 수정이나 전역 무조건 허용 금지.
3. **승인 재사용/재로그인 검증:** 동일 실행 파일 v0.4.2에서 첫 성공 후 재실행·로그아웃/재부팅 동안 추가 권한 팝업이 없는지 확인.
4. **실제 운영 승인:** 안정적 read-only 진단 통과 후에만 사용자가 별도 `ROUTABL_BackupApprovalGate_v0_1.py approve`를 검토. 사용자 명시 승인 전 백업 활성화 금지.
5. **실제 04:30 무인 백업 7일 검증:** 매일 Mac→AES256→NAS CAS 해시/영수증, 실패·중복·NAS 연결 누락, 잠금 상태, 권한 재요청 유무 확인.
6. **NAS 자동 마운트/Keychain:** 재부팅 후 백그라운드 사용자 세션에서 DSM SMB 볼륨과 암호화 이미지 잠금 해제에 대한 비대화형 접근 가능한지 검증.

## 5. 첫 예약 점검
- ChatGPT 기존 `라우터블 첫 자동 백업 검증` 예약을 **`라우터블 v0.4.2 첫 무인 진단 검증`**으로 갱신.
- 2026-11-04 05:30 KST에 04:30 v0.4.2 진단 전용 에이전트 실행 여부를 **읽기 전용** 확인하도록 설정. 예약 자체를 실제 백업 성공으로 오인하지 말 것.
- 기존 NAS/로컬 수동 성공 영수증을 읽기 전용으로 확인하고 Google Drive 작업을 수행하지 않도록 수정.

## 6. 앱/증거 위치
- 앱: `~/Applications/라우터블 백업 권한·안전관리 v0.4.2.app`
- ZIP: `~/ROUTABL-TechAssets/70_EXPORTS/ROUTABL_BackupSafeManager_v0.4.2_20261104.zip`
- v0.4.2 네이티브 소스: `~/ROUTABL-TechAssets/40_WORKING/HEADLESS_NATIVE_V0_4_2/`
- v0.3, v0.4, v0.4.1 앱/소스 원본은 기존 위치에서 보존. **실행 권한 없는 구버전 파일을 덮어쓰지 않음**.
- 실제 실행 이벤트: `~/Library/Logs/ROUTABL-AssetBackup/last_native_launchagent_v04.json`
- 이번 감사기록은 최근 암호화 v0.14 백업 이후 작성됨. v0.4.2 신규 소스와 보고서 자체가 v0.14 NAS 이미지에 이미 포함됐다고 주장하면 안 됨.
