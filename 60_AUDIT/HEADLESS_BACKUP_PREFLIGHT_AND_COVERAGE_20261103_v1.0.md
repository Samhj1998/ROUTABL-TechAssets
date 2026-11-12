# 120. Headless 백업 안전성·보존 범위 실측 — v1.0
기록 시각: 2026-11-03T20:23:06+09:00
판정: **자동 백업 재활성화 보류(HOLD). 읽기 전용 조사 및 합성 모의실행 완료.**

## 기존 중단 및 원인
- 2026-11-03 Terminal 무한 창/개인정보 권한 팝업 사고로 로컬·NAS·Drive 3개 LaunchAgent 중지.
- 원인은 예약 plist가 Python을 직접 실행하지 않고 `/usr/bin/open -gj -a Terminal ...command`를 실행한 GUI 경로.
- 새 후보는 `/usr/bin/python3` 직접 실행, `KeepAlive=false`, `RunAtLoad=false`, `ThrottleInterval=300`, 단일 예약시간.
- 새로운 예약은 **Library/LaunchAgents에 설치·등록·활성화하지 않음**. 기존 3개 비활성화 보존.
- 단일 가짜 subprocess 생성·중복 flock 거부 테스트 통과. 실제 launchd/TCC/Keychain 백그라운드 접근은 미시험.

## 현재 백업 상태 (읽기 전용)
- SSD2TB/NAS 마운트 정상, AES sparsebundle 폴더 존재·마운트 해제.
- 마지막 로컬 성공 영수증: 2026-11-03 07:05 KST (28개 파일).
- 마지막 NAS 복제 성공 영수증: 2026-11-03 07:20 KST.
- Google Drive: 기존 파일 크기 일치 기록만 있고 클라우드 측 해시/복원 검증은 미완료.
- 위 과거 영수증은 이후 생성한 검색 v1.5, 자산대장 v0.7의 백업 완료 증거가 아님.

## v0.7 자산대장 33개 파일 vs 기존 암호화 백업 포함 규칙
| 구분 | 등록 파일 수 |
|---|---:|
| 기존 자동 백업 범위에 포함 가능한 파일 | 5 |
| Mac 검색엔진·SQLite 저장소 위치 (대상 외) | 16 |
| 별도 설치 Mac 앱 (대상 외) | 4 |
| 활성 개발 소스 (대상 외) | 2 |
| 기술자산 Working 및 기타 포함 규칙 외 | 2 |
| 별도 NAS/보존 자산 (대상 외) | 4 |
| 합계 | 33 |

- 현재 포함 가능하다는 뜻은 **백업이 실제 수행됐다는 뜻이 아님**.
- 다른 GitHub·NAS 사본이 존재할 수 있으므로 대상 외 = 유실이라는 뜻이 아님.
- 기존 실제 소스 복사 정책은 `00_GUIDE,20_ORIGINALS,30_REGISTRY,50_VERIFIED,60_AUDIT,70_EXPORTS`만 대상으로 설정됨.
- `40_WORKING`, StudioProjects, 검색 DB, macOS Applications는 대상 밖이며, 설계적으로 보완이 필요.
- 기존 프로그램은 파일명 기반 민감정보 제외로, 암호·인증정보가 완전히 제외됨을 보증하는 것은 아님.

## 실행한 안전 시험
- Python preflight 문법 컴파일·읽기 전용 환경 점검·2개 후보 launchd plist 구조 검증.
- 종속 실제 백업 프로그램을 **실행하지 않는** 가짜 subprocess 단일 수행/잠금 충돌 시험 성공.
- 본 단계에서는 AES 이미지 마운트·암호 해제·NAS 파일 복사·Drive 업로드·복원·launchctl 등록 전부 수행하지 않음.
- 보안키·암호·접속 토큰을 파일·로그로 새로 저장하거나 요청하지 않음.
- 실제 반복 Terminal 창 재발 위험을 없앴다는 **실환경 판정은 아직 불가능**. 안전한 무인 실행 확인이 필요함.

## 재개 조건
1. 자산 등급에 따라 암호화 백업 대상 목록을 확정. 패스키·Firebase Admin SDK JSON·비밀번호는 제외.
2. 일반 소스/검색 스크립트/Working 원본 중 재생성 불가 자산을 별도 보관 대상으로 명시.
3. 실제 새 백업을 **Terminal 없이**, 단발·사용자 승인하에 실행하고 TCC·Keychain 오류 및 종료 후 마운트 해제 확인.
4. 별도 격리 위치에 검증용 파일을 복원한 뒤 SHA-256로 대조. 운영 원본 덮어쓰기 금지.
5. NAS 암호화 보관본 독립 해시 확인 뒤 사용자 동의하에 새 스케줄 설치; Drive는 원격 해시 확인 후 별도 판단.

## 생성물
- 사전 점검기: `00_GUIDE/ROUTABL_HeadlessBackupPreflight_v0_1.py`
- 예약 설정 초안(2개): `40_WORKING/BACKUP_HEADLESS_V0_1/proposed_launchagents/`
- 범위 분석 JSON: `30_REGISTRY/asset_backup_scope_v0.1.json`
- 안내: `00_GUIDE/HEADLESS_BACKUP_RESTART_GATE_v0.1.md`
