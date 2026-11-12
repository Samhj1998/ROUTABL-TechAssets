# v043 릴리스와 운영 수용 설계

## 릴리스 구성

제안 위치는 /Library/Application Support/ROUTABL-AssetBackup/releases/v043/ 및 /Applications의 서명된 관리 앱이다. 실제 경로와 권한은 별도 승인으로 확정한다. 전용 관리 주체만 수정 가능한 상위 디렉터리와 릴리스, 실행 UID, NAS/SSD 쓰기 자격을 함께 검증한다. 현재 확인한 기존 앱은 UID 501 소유, 앱 루트와 바이너리 모드 0700, ad hoc 서명, TeamIdentifier 미설정, 개별 codesign strict 성공이다. 이 관찰은 v043 서명 자격이나 실제 Team ID를 제공하지 않는다.

| 배포·설정 대상 | 필요한 작업 |
| --- | --- |
| ROUTABL_BackupHeadlessSupervisor_v0_3.py | B4 격리 후보에서 운영 감독자 작성. 보호 디렉터리 공통 잠금, 예약·수동 IPC, 실패 시 안전 차단 적용 |
| ROUTABL_MacToNasOneShot_v0_2.py | 운영 실행 후보 작성. 인가된 엔진만 실행하고 상태·exit·timeout·자식 정리 증거를 반환 |
| ROUTABL_BackupEvidenceAdapter_v0_1.py 및 ROUTABL_BackupEvidenceNormalizer_v0_1.py | 가상 출력 어댑터와 실제 영수증 정규화 접합, 실제 입력·권한 검증과 CAS 검증 영수증 추가 |
| backup_runner_candidate.py 및 모든 전이적 Python 모듈 | 운영용 전체 import 목록과 실제 해시를 봉인. fixture_worker, fixture_boundary, 시험용 승인 파일은 배포에서 제외 |
| v043 관리 앱·에이전트·구성 | ROUTABLBackupAgent.swift, ROUTABLBackupManager.swift, Info.plist, Contents/Library/LaunchAgents/com.routabl.assetbackup.native.v043.plist를 별도 신규 릴리스에 빌드·서명. 번들 ID, 프로그램 경로, 04:30, 등록 도메인, 서명 요건을 확인 |
| 신규 승인 파일 | 제안 approval_v043.json. 릴리스 ID, 실행 UID, 서명 요건, 프로그램/전이 의존성 핀, 잠금 경로, 작업·저장 매체 범위, 만료·취소 정책을 고정. 기존 approval_v01.json 보존 |
| 구 진입 및 공유 권한 | 구 관리자에서 v02·v042 등록 관리. 구 .command 및 이전 엔진 직접 호출의 쓰기 경로와 NAS/SSD 접근 자격을 제한하는 설정을 별도 승인 |

DEPENDENCY_PINS.json은 실측 후보 및 운영 참조 해시와 신규 릴리스에서 아직 결정되지 않은 항목을 분리한다. 실제 바이너리 서명은 codesign strict와 지정 서명 요건 및 확인된 Team ID를 검증하고, 서명 후 바이트와 번들 정책을 독립적으로 고정한다. 승인된 신원·팀·최종 v043 바이너리·실제 의존성 세트 미확정 상태에서는 운영 실행을 거부한다.

Apple 제공 /usr/bin/python3와 실제 실행 파일, macOS 빌드, /usr/bin/hdiutil, /usr/sbin/diskutil을 별도 플랫폼 경계로 관리한다. stdlib·동적 로딩·zoneinfo를 포함한 완전한 런타임은 신뢰된 OS/CLT 빌드에 고정하고 변경 시 재승인한다. Python의 사용자 site·PYTHONPATH·임의 .pyc를 허용하지 않는다. 에이전트가 검증 전에 후보 Python을 실행하거나 앱이 사용자 쓰기 가능한 릴리스의 핀을 스스로 생성하면 승인으로 인정하지 않는다.

## 전환 수용 순서

1. 전환 직전 04:30 창 밖, 실행·락·마운트 없음과 최근 정상 영수증을 확인한다. 현재 등록·서명·핀·설정·자격을 기록한다. 회수 계획과 별도 사용자 승인이 전제다.
2. 기존 v02를 해제한다. 등록·실행 프로세스와 재등록 가능 경로를 확인한다.
3. v042만 남았는지 확인한다. 직접 쓰기 우회가 차단되지 않으면 후속 전환을 보류한다.
4. v042를 해제한다. 기존 락과 실행 종료, 이미지 분리 상태를 확인한 뒤 v043을 단일 등록한다. 04:30 라벨·실행 경로·서명·핀을 대조한다.
5. 별도 승인 범위에서 정기 실행을 관찰한다. 최신 대장 및 선택 SHA, 건수와 바이트, 새 로컬 영수증·잠금, 연결된 CAS 완료 및 구성요소 검증 증거를 모두 확인한다. 신규·재사용·잠금 스킵·실패를 구분한다.

실패 시 v043부터 등록 해제하고 신규 프로세스·락·매체 상태를 확인한다. 사전 승인된 v042 단독으로 복귀할 수 있는 경우에만 서명과 핀을 재확인 후 복귀한다. v02 동시 등록은 복원하지 않는다. 안전한 복귀가 확인되지 않으면 자동 실행을 중지하고 Chat 판단을 받는다. 기존 영수증과 백업은 보존한다.

11월 8일 04:30 조사 B는 기존 정기 실행이 실제 최신 v0.27 보호 증거를 남겼는지 읽기 전용으로 검증한다. 이번 B5로 정기 실행 결과를 대체할 수 없다. Step 5-C는 BLOCKED다.
