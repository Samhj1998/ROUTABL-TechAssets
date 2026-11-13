# 자동 백업 예약 해제 발견·복구 기록 (2026-11-13 21:20~21:40 KST)

## 발견
- 11-13 04:30 자동 백업 기록 없음. 마지막 기록: 감독자 상태 11-12 04:30, 수동 성공 11-12 22:58(ASSET_V21_20261112_225825_KST_9870, 1,830개, 표본 복원 15, NAS CAS 완료).
- Mac 잠자기 아님(caffeinate 20시간+ 유지).
- `launchctl print gui/501/com.routabl.assetbackup.native.v042` → "Could not find service": **예약 에이전트 등록 해제 상태**. 시스템 설정 '백그라운드 허용' 스위치는 켜져 있었음(스위치 ≠ 등록).
- 해제 시점·원인 미상(11-12 04:30 이후). 의도적 해제 기록 없음.
- 부수 발견: 관리자 앱 v02와 v0.4.2 동시 실행(전환 계획은 단독 운영 요구), 백그라운드 허용 v0.4·v0.4.1도 켜짐, 검색 서비스 v17·v18 동시 실행.

## 원인 구조
- v0.4.2 관리자 앱은 승인 파일(`approval_v01.json`)이 있으면 새 에이전트 등록을 거부하도록 설계(`registerAgent`). 정상 설치 순서는 '등록 → 승인 파일 생성'. 등록만 풀리면 앱으로 재등록 불가.

## 조치 (사용자 승인·직접 실행)
1. 시스템 설정: 자동실행 준비 v0.2 백그라운드 허용 끔(사용자), v0.4·v0.4.1 끄기 안내.
2. 승인 파일 임시 이름 변경(`.hold`) → 앱 「안전 에이전트 등록」 → `SMAppServiceStatus rawValue 1`(enabled) → 승인 파일 원위치.
3. 원위치 후 승인 파일 SHA-256: `01f2973f0b90f34f522fca0977da3c15aba38667705dc58c6f124c5d6866cff5` (같은 폴더 내 이름 변경만 수행, 내용 변경 없음).
4. 확인: `launchctl print` → path=submitted by smd, state=not running(예약 대기) — **등록 PASS**.

## 미검증·후속
- 실제 백업 실행: 11-14 04:30 결과로 판정(감독자 상태 파일·로컬 스냅샷·NAS CAS).
- 해제 원인 재발 방지: 매일 점검 시 `launchctl print … native.v042` 포함 권장. v02 앱 종료·v0.4/v0.4.1 비활성 확인.
- 교훈(자산 후보): 'UI 스위치 켜짐'은 '예약 등록'을 보장하지 않음. 백업 상태 점검은 예약 존재 + 마지막 실행 기록을 함께 본다.

## 11-14 04:30 결과 (07:02 KST 확인, 읽기 전용)
- 예약 실행: **PASS** — 04:30:31 실행기 시작(`last_native_launchagent_v04.json`, launchAgentRegistrationChanged=false).
- 백업: **FAIL** — 실행기 `BACKUP_FAILED_NO_RETRY`, childExitCode 7, 25.4초. 감독자 v0.2 `FAILED_ONE_ATTEMPT_NO_RETRY`, phase=child, returncode 2.
- 로컬·NAS 결과 파일 갱신 없음(마지막 성공은 11-12 22:58 수동 그대로).
- **원인 특정 불가:** 감독자가 하위 작업(MacToNasOneShot_v0_1)의 출력을 `stdout/stderr=DEVNULL`로 버리고, OneShot은 예외 시 오류 종류 이름만 남긴 채 exit 2로 끝남 → 실패 사유(예: STORAGE_OFFLINE, LOCAL_BACKUP_RECEIPT_NOT_SUCCESS 등)가 어디에도 기록되지 않음.
- 25초 만에 종료 → 저장장치 확인 또는 로컬 백업 초기 단계에서 실패했을 가능성이 높음(추정).
- 사용자 지시(11-13 21:41)에 따라 재제작 설계안 작성: `40_WORKING/backup/BACKUP_V3_REDESIGN/DESIGN_v0.1.md`.
