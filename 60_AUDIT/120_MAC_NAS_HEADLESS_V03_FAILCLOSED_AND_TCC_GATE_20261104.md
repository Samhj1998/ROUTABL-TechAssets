# 120번 Mac→NAS 무인 백업 안정화 v0.3 — TCC 승인·무한 대기 방지

작성 기준: 2026-11-04 KST

## 1. 목표와 확정 범위
- Mac Studio → AES-256 외장 SSD → Synology NAS CAS 증분 보관, SHA-256 검증.
- Google Drive 직접 업로드/다운로드를 ChatGPT 자동 백업 범위에서 제외. NAS Cloud Sync 주간 최종 외부 보관은 사용자 직접 관리.
- 기존 암호화 원본·NAS CAS 기준/증분 영구 보존. NAS CAS 기준 전체 스냅샷 삭제 금지.
- 무인 실행에서 매번 파일 접근 권한 승인 창이 나타나면 **운영 실패**로 판정.

## 2. 발견한 오류
- Mac에서 실제로 등록된 v0.2 SMAppService 진단 에이전트를 1회 실행한 결과 자식 Python이 NAS 디렉터리 접근 위치에서 대기함.
- 사용자 UI 실제 요청: **‘라우터블 백업 자동실행 준비 v0.2’이(가) 네트워크 볼륨의 파일에 접근하려고 합니다.** 최초 권한이 필요하다는 직접적인 증거.
- `sample`에서 `__opendir2`, `__open_nocancel` 등이 관찰됨. TCC 허용 창 때문인지 SMB 연결 지연이 겹쳤는지는 추가 구분 필요.
- 자식 PID 28565 수동 종료 뒤 서비스 PID 종료. 정상 무인 실행으로 인정하지 않음.
- v0.2 및 기존 3개 LaunchAgent 모두 **disabled**, v0.3 아직 미등록.
- 기존 v0.1 감독 프로그램은 **승인 존재 여부를 검사하기 전에 NAS 마운트·CAS 디렉터리 접근**을 수행하는 순서상의 오류가 있었음.

## 3. 새 구현 (기존 버전 수정/삭제 없음)
1. `00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_2.py`
   - 승인 여부 로컬 선검사. 승인 파일 부재 시 NAS/SSD 접근 없음.
   - `check`, `probe`, `simulate`, `scheduled` 구분.
   - `probe`는 승인 없거나 무결성 불일치 시 실패-폐쇄; 승인된 경우에만 네트워크 접근 검사.
   - 실제 백업의 자식 프로세스를 독립 프로세스 그룹으로 실행하고 시간 제한 시 해당 그룹 전체 종료하도록 보완.
   - 실제 백업 완료 시에도 영수증 연계를 검증하지 못하면 성공 판정 금지.
2. `40_WORKING/HEADLESS_NATIVE_V0_3/ROUTABLBackupAgent.swift`
   - Apple Swift 네이티브 에이전트. 처음부터 승인 파일 부재를 확인해 즉시 종료.
   - 사용자 승인 후에만 로컬 서명된 코드 해시 고정 확인 → 최대 20초 NAS 접근 사전 진단 → 실제 Mac→NAS 백업 단발 실행.
   - 보호된 파일 접근이 응답하지 않더라도 부모 프로세스가 제한시간 후 자식을 종료.
   - 성공 시 현재 회차 `SUCCESS_VERIFIED` 영수증까지 확인.
   - 상태는 `~/Library/Logs/ROUTABL-AssetBackup/last_native_launchagent_v03.json`에 기록; 일반 사용자의 기존 영수증을 덮어쓰지 않음.
3. `40_WORKING/HEADLESS_NATIVE_V0_3/ROUTABLBackupManager.swift` 및 별도 v0.3 앱
   - macOS 공식 SMAppService 사용, `Contents/Library/LaunchAgents`에 구성.
   - `NSNetworkVolumesUsageDescription`, `NSRemovableVolumesUsageDescription` 포함.
   - 고정 Bundle ID `com.routabl.assetbackup.manager.safe`, agent `com.routabl.assetbackup.native.safe`.
   - KeepAlive=false, RunAtLoad=false, 오전 04:30 한 번 실행하는 구성. 현재 **미등록/비활성화**.
   - 권한 설정을 자동으로 수정하거나 OS ‘허용’ 버튼을 클릭하지 않음.
   - 구형 v0.2 앱/코드·예전 스케줄러는 보존.
4. `00_GUIDE/ROUTABL_BackupApprovalGate_v0_1.py`
   - `review`는 현재 앱 서명·스케줄 정책·핵심 실행파일 SHA-256 점검만 수행.
   - `approve`는 Mac 사용자 **실제 대화형 터미널에서 특정 승인 문구를 입력**하기 전까지 승인 파일 생성 금지.
   - 이번 자동화 과정에서는 승인 파일 생성/실제 백업 예약 활성화를 수행하지 않음.

## 4. 검증 결과
- v0.2 감독 프로그램 `check` 및 `probe` 모두 승인 파일이 없을 때 DISARMED 및 `network_volume_accessed=false` 확인.
- v0.3 Swift 네이티브 실행 파일 문법·컴파일 성공.
- `--local-probe`: 실제 Mac 사용자 환경에서 PASS, NAS/SSD 권한 요청 없이 실행.
- `--watchdog-selftest`: 의도적으로 잠드는 격리 프로세스를 제한시간에 종료 PASS.
- 초기 v0.3 이벤트 파일 미기록 오류 확인 및 수정. `LOCAL_SAFE_ACCESS_OK` 실제 JSON 상태 파일 저장 PASS.
- v0.3 앱 Info.plist·LaunchAgent plist lint PASS, ad-hoc 코드 서명 검증 PASS, 설치 사본 서명 검증 PASS.
- Mac GUI에서 v0.3 앱을 실제 열고 `로컬 안전 진단` 버튼을 눌러 `로컬 진단 통과 · NAS 권한 별도 승인 필요` 표시 PASS.
- `ROUTABL_BackupApprovalGate_v0_1.py review`: 실제 앱 서명·승인 부재·04:30 스케줄·Drive/삭제 미허용 점검 PASS.
- v0.3 앱은 설치했지만 **시스템 백그라운드 등록은 하지 않았고 사용자가 권한을 새로 승인하지 않음.**
- 사용자 계정의 macOS 코드 서명용 Developer ID 인증서 목록: **0 valid identities**. 현재 v0.3 앱은 ad-hoc 서명. 버전 업데이트·재서명 시 기존 TCC 승인이 유지된다고 보장할 수 없으므로 공식 개발자 서명(또는 변경 없는 검증된 로컬 배포)을 검토해야 함.

## 5. 남은 사용자 공동해결 관문
1. **최초 macOS 권한 승인**: 새 v0.3을 최종 고정한 후 신뢰 가능한 앱 식별자/서명을 확인하고, 정확히 어떤 앱이 NAS/SSD에 접근하는지 확인한 다음 사용자만 최초 승인. OS TCC.db 수정/권한창 자동 클릭 금지.
2. **실제 백그라운드 진단 단발**: v0.3 서비스 등록 뒤 예약 또는 1회 실행에서 권한 팝업 없이 정해진 시간 내 종료하는지, 상세 에이전트 영수증이 기록되는지 확인.
3. **운영 전환 시 최종 승인**: `ROUTABL_BackupApprovalGate_v0_1.py approve`는 1·2가 통과한 후에만 사용자가 실행. ChatGPT가 임의로 approval 파일 생성 금지.
4. **실제 무인 AES→NAS 백업 연속 검증**: 7일 동안 예약 지연·누락·중복·권한 재요청·NAS 재연결·재부팅 뒤 자동 마운트/Keychain 등 확인. 확인되지 않은 사항은 완료로 판정 금지.
5. **자동 장애 알림**: 네트워크/SSD 실패·NAS 공간 부족·성공 영수증 누락 시 사용자에게 알릴 채널 및 개인정보 수준을 별도 협의. 아직 구현·활성화되지 않음.

## 6. Apple 참고자료
- https://developer.apple.com/documentation/servicemanagement/smappservice
- https://developer.apple.com/documentation/servicemanagement/smappservice/register()
- https://developer.apple.com/documentation/bundleresources/information-property-list/nsnetworkvolumesusagedescription
- https://developer.apple.com/documentation/bundleresources/information-property-list/nsremovablevolumesusagedescription
- 최초 macOS 접근 승인 후 사용자 선택은 macOS가 기억하지만, 앱 식별·코드 서명·볼륨 접근 주체가 안정적으로 유지된다는 별도 조건이 필요함.

## 7. 기존 성공 백업 보존
- 마지막 실제 검증된 로컬→NAS 백업 기준 `asset_manifest_v0.13.json`의 **73개 자산 / 3,308개 파일**.
- NAS 실제 증분 및 AES-256 복원 268개 구성 파일 전수 확인, 복호화 내부 파일 3,308개 전수 SHA-256 PASS.
- 운영 백업 스냅샷, CAS 기준 전체 스냅샷 `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`, Firebase, GitHub, Android 프로젝트의 기존 자료 미변경.
