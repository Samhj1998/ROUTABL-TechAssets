# 120번 백업 무인 실행 — 권한 팝업과 백그라운드 대기 문제

기록 시점: 2026-11-04 KST

## 사용자 요구
- Mac Studio 앞에 사람이 없어도 Mac→SSD AES-256→Synology NAS 백업이 정상 작동해야 함.
- macOS 접근 허용 팝업이 매일 반복되어서는 안 됨.
- 보안 경고를 우회하는 자동 클릭이나 전역 무조건 허용은 금지.
- Google Drive는 Synology Cloud Sync 주간 최종 보관으로만 사용, ChatGPT 작업 범위에서 제외.

## 시험에서 실제 확인한 사실
- SMAppService v0.2 진단 LaunchAgent `com.routabl.assetbackup.native.v02` 등록 상태.
- 수동 `launchctl kickstart` 1회에서 네이티브 에이전트 PID 28563 및 자식 Python 28565 생성, 이후 정상 종료하지 않고 대기.
- 자식 Python 프로세스를 `sample`로 검사했을 때 `__opendir2` / `__open_nocancel`의 디렉터리 접근에 머무른 흔적 확인. 이것만으로 TCC 거부인지 NAS SMB 지연인지는 단정할 수 없음.
- 사용자 macOS 권한 요청 창이 나타난 상황. 실제 앱/접근 대상에 대한 최소 권한 승인 필요성 있음.
- Python 자식 PID 28565 안전 종료 후 부모 에이전트도 종료 확인. 마지막 종료 코드는 15(시험 중단에 따른 종료)이며 성공적 무인 완수로 판정하지 않음.
- 운영 로컬 AES 백업, NAS 증분, 기존 성공 영수증 변경 없음.
- 새 진단 에이전트 v0.2는 **`launchctl disable gui/501/com.routabl.assetbackup.native.v02`로 비활성화**하여 예정된 04:30 시각에 재실행·권한 재요청을 방지.
- 기존 `com.routabl.assetbackup.daily`, `.nas.daily`, `.drive.daily`도 비활성화 유지.
- 자동 백업 승인 파일 `~/Library/Application Support/ROUTABL-AssetBackup/approval_v01.json` 없음.

## 정상 운영에 필요한 해결 방향
1. 진단 앱·운영용 백그라운드 실행파일에 **고정된 코드 서명 및 앱 식별자**를 사용하고 임의 재빌드·재서명 때마다 실행 주체가 달라지지 않게 관리.
2. `Info.plist`에 네트워크 볼륨 및 외장 저장장치 접근 목적 설명(`NSNetworkVolumesUsageDescription`, `NSRemovableVolumesUsageDescription`)을 포함하고 Apple 사용자 동의 흐름을 따름.
3. macOS의 `시스템 설정 → 개인정보 보호 및 보안 → 파일 및 폴더`에서 **정확한 프로그램 이름**에 대한 NAS/외장 SSD 권한을 최초 한 번만 사용자 승인. 필요한 경우에만 더 넓은 권한을 개별 검토, 전체 디스크 접근 무조건 허용 금지.
4. Python 도구의 백그라운드 접근과 SMB 마운트 지연을 구분하기 위한 **단계별 제한시간 있는 점검**을 도입. 파일 목록 조회가 무기한 대기하면 안 됨. 기존 v0.2를 단순 재시작하지 않음.
5. 최소 권한 승인이 유지되는지 로그아웃/재시작 후 **백업 없이 진단만 단발 실행**하여 시험하고, 성공 시에만 별도의 명시 승인으로 실제 백업 운영을 활성화.
6. NAS 연결 상실·SSD 미연결·동시 실행·Keychain 잠금·권한 회수/변경·디스크 용량 부족의 실패안전 동작을 운영 모드에서 검증.
7. 7일 연속 무인 백업 성공/누락/재시도 확인 전까지 자동 운영 완료 주장 금지.

## 보안 및 보존
- 사용자가 허용을 눌렀다는 전제 없이, 현재는 신규 에이전트 비활성화.
- TCC.db 직접 변경, 무한 재시도, 자동화된 허용 클릭, 앱 인증 무력화, 비밀번호 공유 금지.
- 사용자가 실제로 올린 권한 창은 매뉴얼로 검토하되, 요청 프로세스와 접근 대상의 정확한 문구가 확인되지 않으면 승인 여부를 단정하지 않음.
