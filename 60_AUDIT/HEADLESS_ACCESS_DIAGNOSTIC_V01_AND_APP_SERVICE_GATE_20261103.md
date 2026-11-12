# 120. 무인 기술자산 백업 접근 권한 진단 및 안전한 재개 조건

기록일: 2026-11-03 KST  
판정: **일반 사용자 컨텍스트 사전 점검 13/13 통과, 독립 launchd 권한 오류 원인 미확정, 자동 백업 활성화 금지 유지.**

## 1. 배경과 원본 증거

- macOS 27.2, Mac Studio 사용자 UID 501 확인.
- 2026-11-03 21:45~21:46 기존 `launchctl submit` 일회성 서비스 `com.routabl.assetbackup.v21.oneoffcheck`가 약 10초 간격으로 총 6차례 시작/종료됨.
- 6번의 오류 기록 모두 `{"result":"FAILED_SAFE","failure_type":"PermissionError"}`.
- 시스템 로그에는 `launchd`가 `python3` 프로세스를 다시 생성한 시각이 직접 표시됨. 해당 서비스는 21:46:13경 제거, 이후 재확인에서 존재하지 않음.
- 접근이 필요한 상태 폴더·백업 코드·사용자 프로젝트의 계정 소유자와 기본 Unix 파일권한은 적절해 보임.
- 기존 코드 `ROUTABL_HeadlessDailyGate_v0_3.py`는 최상위 예외 처리에서 **실패한 구체적 단계(파일·연산)**를 기록하지 않았으므로 당시 어떤 접근에서 PermissionError가 발생했는지는 식별 불가능함.
- TCC 관련 통합 로그를 시간·키워드로 제한해 확인했으나 확정할 만한 거부 메시지는 발견되지 않음. **TCC 원인 확정 또는 TCC 이상 없음의 증거가 아니다.**
- 기존 Mac/NAS/Drive 자동 예약 3개는 disabled 유지. v2.1 신규 후보 2개도 설치하지 않음.

## 2. 새 별도 진단 도구

`~/ROUTABL-TechAssets/00_GUIDE/ROUTABL_HeadlessAccessDiagnostics_v0_1.py`

- `check`: **읽기 전용** 13단계 경로 접근 검증. 프로그램 실행과 자산 원본 접근을 분리.
- 단계: 사용자 계정, 로그 디렉터리, 로컬/NAS 성공 영수증, 최신 자산대장 읽기, 등록 파일 61개 메타데이터, 백업 스크립트, StudioProjects, SSD, NAS, NAS 증분 기준 목록, 검색 DB, 미설치 예약 설정 2개, AES-256 이미지의 비밀번호 불필요 메타데이터.
- 실제 결과: `MANUAL_CONTEXT_ACCESS_OK__LAUNCHD_TCC_NOT_PROVEN`, 13/13 PASS.
- 별도 `simulate-denial`: 파일 접근 범주 5개에 가상 EACCES 삽입, 각 시험에서 첫 오류 즉시 중단(exit 21), 동일 예외 재시도 없음. 오류 출력은 범주·예외명·errno만 포함.
- 어떠한 모드도 launchctl 등록/실행, Terminal 앱 열기, AES 이미지 마운트, Keychain 잠금해제, NAS 복제, 실데이터 백업, macOS 개인정보 접근 설정 변경을 수행하지 않음.

## 3. 원인 가능성 평가 — 단정 금지

1. 일반 사용자 환경과 `launchd` 서비스 실행 환경의 macOS Privacy/TCC 권한 귀속 차이.
2. 외장 SSD/네트워크 NAS 접근이 독립 실행에서 제한되거나 해당 순간 마운트 상태가 다를 가능성.
3. `~/ROUTABL-TechAssets`/로그 폴더의 접근 과정, 개별 파일 또는 보조 Python 실행기의 권한 차이.
4. macOS 27.2와 `/usr/bin/python3` 서명/실제 실행 파일 간의 서비스 정체성 문제.

**위 항목은 가설**이다. 출처 및 오류 지점이 특정되지 않았으므로 임의로 전체 디스크 접근 권한을 허용하거나 TCC 데이터베이스를 조작해서는 안 된다.

## 4. 안전한 재설계 원칙

- 이전에 10초마다 재실행된 `launchctl submit`은 **다시 사용하지 않는다**.
- 사용자에게 구분 가능한 서명된 Mac 앱/전용 헬퍼 형태를 우선 검토하고, Apple ServiceManagement/SMAppService의 사용자 인지·승인 통로를 사용한다.
- 실행 서비스는 명시적 일정 기반, `RunAtLoad=false`, `KeepAlive=false`, 원본과는 별도 로그, 초깃값 비활성화.
- 먼저 실제 백업을 **절대 수행하지 않는** 독립 실행 컨텍스트에서 단계별 접근 프로브를 단발로 검증. 실패 지점과 errno만 출력하고 중단.
- 사용자 승인이 필요한 macOS 권한은 해당 앱에 한정해 최소 범위로 안내. 앱과 무관한 Python·Terminal의 무제한 전체 디스크 접근 설정은 자동 적용하지 않는다.
- 실제 암호화 저장 시험은 권한 프로브 성공 후, 원본 보존·마운트 자동 해제·암호화 영수증·SHA-256·NAS 동일 회차 검증을 모두 충족할 때만 진행.
- 무인 재실행·예약 설치는 별도의 사용 승인 및 실환경 성공 뒤에 진행한다.

## 5. 기술자산 보존 경계

- 검증된 최신 실백업 기준은 자산대장 **v0.9**의 48개를 포함한 로컬 AES-256 3,282개 파일 및 NAS 암호화 이미지 141개 구성 파일이다.
- 현재 자산대장 v0.11의 61개 항목과 이후 생성된 신규 진단 스크립트는 **마지막 검증된 AES 백업에 포함되지 않음**.
- NAS 내용 기반 증분 기준 목록은 141개 암호화 구성 파일의 SHA-256 검증 통과. 향후 증분 작업은 기준 NAS 전체 백업을 참조하므로 **기준 백업 삭제·이동 금지**.
- 실제 새 암호화 변경 회차의 증분 실백업, CAS 재조립·복호화 전체 복원은 미검증.
- Google Drive v2.1 오프사이트 보관 검증 및 검색 v1.5 새로고침 버튼 사용자 확인도 미완료.

## 6. 이번 작업의 변경 내역

- 새 진단 파일 1개와 이 감사 보고서, 별도 운영 안내서/자산대장 등록만 추가.
- **기존 기사·고객 앱, Firebase, GitHub, NAS 보관본, 스크립트 v2.1, launchd 설치 설정, macOS TCC 권한은 변경하지 않음.**
- 예약 작업을 설치하거나 켜지 않았으며 사용자의 보안키·관리자 JSON·암호는 요구하거나 기록하지 않았음.

## 참고: Apple 공식 기술 문서

- Creating Launch Daemons and Agents: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
- Managing ongoing background processes: https://developer.apple.com/documentation/appkit/managing-ongoing-background-processes-in-your-mac
- Service Management: https://developer.apple.com/documentation/servicemanagement
- Accessing files from the macOS App Sandbox: https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox
