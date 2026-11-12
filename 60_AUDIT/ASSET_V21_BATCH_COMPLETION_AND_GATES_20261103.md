# 120번. 기술자산 백업 v2.1 일괄 실행·무결성·자동화 관문 보고서

작성 기준: 2026-11-03 KST  
결론: **로컬·NAS AES-256 실제 백업 PASS, 최신 자산 및 영수증 연결 PASS, launchd 무인 실행 HOLD, NAS 복호화 전체 검증 HOLD, Google Drive 원격 백업 미완료.**

## 1. 실제 작업 — 로컬 AES-256
- 새 독립 프로그램: `00_GUIDE/ROUTABL_SelectiveSecureBackup_v2_1.py`
- 기준: `asset_manifest_v0.9.json`에 등록된 **48개 자산**. 해당 JSON 자체의 SHA-256:
  `88008d8cd7f0deb44e9708fc004abf42998b2ee52e55470d48e72f2579699636`
- 선택한 소스 전체를 대표하는 SHA-256:
  `ec65b6d643392a1ca4c9fce7985e46ee7ae85fdeecca2153c8d99d5f0320d8ef`
- 선택 파일 **3,282개**, 원본 합계 **518,882,082바이트**. 등록 기술자산 48개 모두 포함.
- 스냅샷: `ASSET_V21_20261103_214028_KST_24533`.
- 파일별 SHA-256 일치, 소형 파일 15개 격리 복원 검증.
- 파일 원본은 변경하지 않았고 기존 SSD 암호화 이미지에 새 스냅샷 추가, 종료 후 이미지 정상 잠금/마운트 해제.
- 로컬 성공 영수증 `~/Library/Logs/ROUTABL-AssetBackup/last_selective_v21_result.json`
- 스냅샷 영수증 SHA-256: `66c6d86f5cdb5b629ed8f716c9a150ebc76e2aa49633d56f298427f9e4713240`

## 2. 실제 작업 — NAS 독립 암호화 복제
- 새 독립 프로그램: `00_GUIDE/ROUTABL_SelectiveNasCopy_v2_1.py`.
- NAS 새 스냅샷: `NAS_MANUAL_ASSET_V21_20261103_214221_KST_24639`.
- 암호화 sparsebundle **141개 구성 파일**, **1,128,457,076바이트**.
- NAS 전체 구성 파일 SHA-256 일치, NAS 영수증 SHA-256 일치.
- NAS 영수증이 최신 로컬 스냅샷 이름 및 로컬 영수증 SHA-256과 직접 연결되었음을 검증.
- NAS 스냅샷을 독립 SSD 시험 폴더에 전체 복원하고 구성 파일 141개 SHA-256과 복원 이미지 AES-256 구조 모두 확인. 시험 파일은 검증 후 삭제.
- NAS 성공 상태 영수증: `~/Library/Logs/ROUTABL-AssetBackup/last_selective_nas_v21_result.json`
- NAS 영수증 SHA-256: `6d69eff73302dd525ad9d90e26717c3c5b9edf79845521bf31895197a84ec837`
- 기존 NAS 스냅샷과 백업 보존본을 덮어쓰거나 삭제하지 않음.

## 3. 백업 중복 실행·영수증 교차검증
- 새 안전 관문: `00_GUIDE/ROUTABL_HeadlessDailyGate_v0_3.py`.
- 지정 날짜 일치뿐 아니라 **현행 자산대장 SHA-256** 및 **현행 소스 파일 선택 목록 SHA-256**까지 확인.
- NAS 영수증은 로컬 스냅샷 이름, 로컬 영수증 SHA-256, 자산대장 SHA-256, 파일 목록 SHA-256 모두 일치해야 정상 인정.
- 단위시험: 자산대장 해시 변경/선택 파일 변경/NAS 영수증의 다른 회차 연결을 거부함.
- 실제 작업 직후 안전 관문의 'local' 및 'nas' 상태가 각각 `SKIPPED_CURRENT_SNAPSHOT_VERIFIED`, `SKIPPED_NAS_LINKED_TO_CURRENT_LOCAL`로 나와 중복 실행 방지 검증 통과.

## 4. Terminal 없는 무인 macOS launchd — **재개 보류**
- v2.1용 LaunchAgent 설정 후보 2개를 `40_WORKING/BACKUP_HEADLESS_V0_3/proposed_launchagents/`에 **초안으로만** 작성. 구문 검사 PASS.
- 새 후보는 Terminal.app을 열지 않고 Python 프로그램 직접 실행, RunAtLoad=false, KeepAlive=false.
- `launchctl submit` 방식의 **1회 읽기 전용 점검**에서 macOS 독립 실행 환경은 `PermissionError`로 실패.
- 해당 임시 서비스가 오류 종료 후 재시도된 점을 확인하여 즉시 제거했고, 재확인 시 서비스 미존재·관련 프로세스 없음.
- 반복 Terminal 창이 발생하지는 않았지만 **반복 실행 위험이 확인되었으므로 launchctl submit 방식은 재사용 금지**.
- 실패 원인은 접근 허용 범위 확인이 필요하며 임의로 macOS 권한을 우회하거나 보안 설정을 변경하지 않음.
- 기존 `com.routabl.assetbackup.daily`, `com.routabl.assetbackup.nas.daily`, `com.routabl.assetbackup.drive.daily`는 모두 계속 disabled. 새로운 예약도 설치하지 않음.

## 5. 보안·복원 검증 경계
- **미완료:** NAS에서 복원한 AES 이미지 자체를 별도 읽기 전용으로 복호화·마운트한 다음 내부 3,282개 기술자산을 검증하는 작업. 원격 실행 안전 검사가 차단되어 우회하지 않음.
- 현재 입증: 로컬 암호화 이미지 안에 3,282개 파일을 실제 저장했고 SHA-256을 대조함. NAS 암호화 이미지 자체의 전체 복원·해시·암호화 구조도 검증함.
- 패스키·비밀번호·Firebase Admin SDK 원본은 의도적으로 수집하지 않음. 그러나 ZIP/PDF/SQLite 등 전체 바이너리 안의 기밀정보 부재를 자동 정규식으로 보증하지는 못함.

## 6. Google Drive 외부 백업
- 연결된 Google Drive `ROUTABL-TechAssets-Backup` 폴더를 서버측 목록으로 직접 확인.
- 조회 결과: 기존 업로드 시험용 소형 텍스트 파일 1개가 확인됨.
- **v2.1 AES 암호화 이미지의 Google Drive 업로드/다운로드/해시 검증 없음**. 백업 완료 주장을 하지 않음.
- Google Drive는 Mac·SSD·NAS 모두 사용 불가할 때를 대비한 마지막 오프사이트 수단으로 분리 유지.

## 7. 운영상 새로 발견한 개선 필요 사항
- 현재 NAS 복제 방식은 새 암호화 이미지 스냅샷이 늘어날 때마다 `sparsebundle` 전체를 새 폴더로 복제하므로 용량·대역폭 사용이 증가함.
- v2.1 NAS 단일 복사 제한을 19GB로 조정했으나 이는 임시 안전 상한일 뿐 **증분 복제 또는 독립 보존주기 정책을 대체하지 못함**.
- 자동 예약 재개에 앞서 launchd 백그라운드 권한 문제와 실패 시 중단 정책, NAS 보존·용량 계획이 필요.
- 검색 v1.5 '색인 새로 고침'은 자동 API 시험은 통과했으나 사용자 화면 버튼 클릭 실기기 검증은 별도로 남음.

## 8. 보존
- 기존 v2.0 로컬·NAS 스냅샷, 자산대장 v0.9, 기사·고객 앱, Firestore, GitHub 코드 변경·삭제 없음.
- 본 보고서와 뒤이어 발행하는 자산대장 v0.10은 **v0.9 기준 AES v2.1 스냅샷 생성 이후의 자료**이므로 해당 스냅샷에 포함됐다고 주장하지 않음.
