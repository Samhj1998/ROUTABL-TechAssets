# SelectiveSecureBackup v2.2 초안 — 시험 결과와 교체 절차 (2026-11-12)

## 왜
자동 백업(매일 04:30)이 며칠째 실패. v2_1이 두 조건에서 멈춤:
① 옛 프로젝트 4개 폴더 없음(2026-11-11 정리) ② 등록 자산 SHA 변경 시 전체 중단(살아 있는 파일이라 계속 바뀜)

## 바뀐 점 (v2_1 대비 61줄)
- 등록부: 30_REGISTRY/asset_manifest.json 우선 (없으면 가장 높은 v0.N)
- 등록 자산: SHA 바뀜 → 지금 파일 백업 + `registry_drift_asset_ids` 기록 / 없음 → `registry_missing_asset_ids` 기록 / 같은 경로 옛 등록 → 한 번만
- 대상 프로젝트: 현재 주요 앱 6개 (고객등록앱·분석앱 추가, 옛 4개 제외)
- 그대로: 비밀값·고객 전화 차단, 파일·전체 용량 제한, AES-256 확인, 스냅샷 SHA 검증, 복원 시험, 결과 파일 이름(last_selective_v21_result.json)
- 시험용 환경변수 ROUTABL_HOME·ROUTABL_PATH_MAP (Mac에서는 설정하지 않음 → 기본값)

## 원격 시험 (plan 모드, 디스크 쓰기 없음)
- 결과: DRY_RUN_ONLY 정상, 2.3초, 1,804개 파일 54.5MB (등록 168·프로젝트 1,506·관리 130)
- drift 5 / 같은 경로 옛 등록 4 / 차단 3(고객 전화 패턴 2 포함) / missing 25 (원격 셸에서 안 보이는 ~/Library·NAS 경로 → Mac에서 다시 확인)
- 호환: HeadlessDailyGate_v0_3이 쓰는 inventory·digest·selection_digest·REGISTRY 그대로. SelectiveNasCopy_v2_1은 등록부를 읽지 않음

## 저녁 교체 절차 (Mac 앞, 약 10분)
1. 진단 앱으로 마지막 성공 시각·실패 원인 확인
2. 터미널: `python3 ~/ROUTABL-TechAssets/40_WORKING/backup/SELECTIVE_BACKUP_V2_2_DRAFT_20261112/ROUTABL_SelectiveSecureBackup_v2_2.py plan` → missing 개수 확인
3. 교체: v2_2 내용을 00_GUIDE/ROUTABL_SelectiveSecureBackup_v2_1.py에 덮어씀 (게이트가 이 파일 이름을 부름. 승인 파일의 SHA 고정 대상 아님. 원본은 git에 있음)
4. 수동 1회 실행 → SSD 백업 성공·NAS 복사 성공 확인
5. 다음 날 04:30 자동 실행 결과 확인
되돌리기: `git checkout p1-baseline-20261112 -- 00_GUIDE/ROUTABL_SelectiveSecureBackup_v2_1.py`
