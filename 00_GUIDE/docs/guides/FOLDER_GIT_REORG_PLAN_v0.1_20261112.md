# 기술자산 폴더 git 방식 정리 계획 v0.1 (2026-11-12)

목표: 사본 대신 변경 이력. 최신본은 하나, 과거는 git 이름표로. 간결·빠름·토큰 최소.
원칙: 단계마다 되돌릴 수 있게 → SHA 검증 → 승인 → 정리. 삭제는 매번 사용자 승인. 단계 끝마다 v1.8 색인 새로 고침.

## 현황 (2026-11-12)
- TechAssets 8.1GB: 20_ORIGINALS 7.5GB(큰 원본·암호화본), 40_WORKING 595MB, 30_REGISTRY 등록부 사본 32개+조회DB 18개
- 내용이 같은 파일 1,004개 (v1.8 색인 기준)
- 홈 폴더 121_* 임시 폴더 약 30개 (미조사)
- v1.8 검색은 폴더 구조와 무관 → 정리해도 새로 고침만 하면 됨

## 단계
- P1 git 시작 (비파괴): TechAssets를 git 저장소로. 텍스트만 추적. 제외: 20_ORIGINALS, 80_RUNTIME, *.sqlite, *.sparseimage, *.zip, _to_delete. 첫 커밋 = 현재 상태 그대로
- P2 등록부 하나로: asset_manifest.json 한 파일에 v0.1~v0.32를 순서대로 커밋, 이름표 registry-v0.N. 모든 이름표가 원래 SHA와 일치하는지 검증 후 사본 32개를 보관함으로. 조회DB는 최신 1개만 생성
- P3 40_WORKING: 작업별 폴더를 주제별로 묶고, 버전 폴더(_V01·_R01·v0_4_1 등)는 git 이력으로. 같은 내용 파일은 하나만
- P4 00_GUIDE: 원칙·안내·스크립트 분리. 옛 스크립트 버전(_v1_0, _v1_1…)은 최신만 남기고 이력으로
- P5 홈 폴더 121_* 임시 폴더: 내용 조사 → 가치 있는 것만 TechAssets로 커밋, 나머지는 보관함
- P6 앞으로의 규칙: 텍스트는 _vN 사본을 만들지 않고 커밋. 큰 파일은 20_ORIGINALS에 두고 SHA로만 참조

## 진행 기록
- 2026-11-12 15:2x P1 완료: git 시작, 첫 커밋 62da46f, 이름표 p1-baseline-20261112. 추적 679개(텍스트), .git 7.9MB, fsck 이상 없음. 이동·삭제 없음
  - 제외: 20_ORIGINALS·80_RUNTIME·*.sqlite·*.pdf·*.zip·암호화본·비밀 파일·고객 데이터 덤프(CUSTOMER_DONG plan*.json)·private/
  - git 임시·잠금 파일 정리를 위해 이 폴더 삭제 권한 승인(이 세션 한정)

- 2026-11-12 15:3x P2 완료 (사용자 승인): 기준 등록부 30_REGISTRY/asset_manifest.json 하나 + 이름표 registry-v0.1~v0.32 (32/32 SHA 일치)
  - 옛 사본 v0.1~v0.31·조회DB v0.1~v0.17 → 30_REGISTRY/_archive_versions/ (삭제 아님)
  - 호환용 asset_manifest_v0.32.json 유지: 정기 백업 SelectiveSecureBackup_v2_1·검색 v1.6/v1.7이 v0.N 파일을 찾음
  - 검색 v1.8: asset_manifest.json 우선 읽기, 보관함 제외, 대표본 삭제 시 중복본 재색인 수정
  - v1.8 코드(.py)도 git 추적 (실행 데이터는 계속 제외)

- 2026-11-12 15:4x P3 완료 (사용자 승인): 40_WORKING 54개 → search·backup·ai_loop·customer 4개 묶음. 내용 변경 없음, git 이름 변경으로 이력 유지
  - 대응표 40_WORKING/PATH_MAP_P3_20261112.tsv. 등록부 v0.33(이름표 registry-v0.33): 자산 19개 경로 갱신, previous_paths 보존. 등록부 상태 이동 전후 동일
  - 호환 사본 v0.32 → 보관함, asset_manifest_v0.33.json으로 교체. 조회DB v0.19
  - 사고·조치: 경로가 바뀌며 고객 데이터 제외 규칙(40_WORKING/CUSTOMER_DONG_*/plan*.json)이 안 맞아 plan.json 3개가 커밋됨. P1부터 plan.json.review.csv(업체명·주소)도 규칙 밖이었음 → 규칙을 **/CUSTOMER_DONG_*/plan* 로 바꾸고 이력 전체에서 제거(filter-branch, gc). 남은 객체 0, 등록부 이름표 33개 SHA 재검증 통과. 로컬 저장소 밖으로 나간 적 없음
  - 교훈: 제외 규칙은 경로가 아니라 이름 패턴(**/)으로. 폴더 이동 전 git check-ignore로 확인
  - 검색 v1.8 새로 고침: 옮겨진 458개 재색인, 문서 수 동일(3,046)

- 2026-11-12 15:5x 백업 점검 (읽기만, 변경 없음):
  - 자동 백업 경로(매일 04:30): 백업 앱 v0.4.2 → 00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_2.py → 승인 파일이 SHA로 고정한 MacToNasOneShot_v0_1·NAS_ContentAwareBackup_v0_2·HeadlessDailyGate_v0_3 → SelectiveSecureBackup_v2_1(로컬 SSD AES)·SelectiveNasCopy_v2_1(NAS)
  - SelectiveSecureBackup_v2_1 실패 조건 2개가 현재 충족: ① 옛 프로젝트 4개 폴더 없음(2026-11-11 정리) → PROJECT_MISSING_OR_SYMLINK ② 등록부 자산 5개 SHA 변경 → VERIFIED_REGISTRY_SOURCE_CHANGED
  - 결론: 자동 백업은 2026-11-11 이후 실패 중일 가능성이 높음 (로그는 ~/Library라 원격 확인 불가)
  - 주의: 00_GUIDE의 위 스크립트 6개는 이동·수정 금지 (경로·SHA 고정)
  - P3b·P4 보류 사유: 옮길 대상에 백업이 요구하는 등록 자산이 포함됨 → 백업 수리 후 진행

- 2026-11-12 23:0x 자동 백업 수리 완료 (Mac 앞, 사용자 실행): 마지막 성공 11-06 → 이후 매일 실패. v2.2를 SelectiveSecureBackup_v2_1 자리에 반영(e831f67)
  - Mac plan: 1,830개 546MB, missing 0, drift 6 / 수동 실행: SSD 22:58 SUCCESS(ASSET_V21_20261112_225825_KST_9870), NAS CAS 23:01 SUCCESS
  - 확인 예정: 11-13 04:30 자동 실행 결과 (승인 고정 스크립트 변경 없음)
  - P3b·P4 보류 해제 (v2.2는 등록 자산이 사라지거나 바뀌어도 기록만 하고 계속 진행)

## 다음 행동
- 등록부 갱신 방법(앞으로): asset_manifest.json 수정 → 커밋 → 이름표 registry-v0.N. v0.N 사본은 만들지 않음
- 남은 호환 사본 v0.32 제거 조건: 백업 스크립트가 asset_manifest.json을 읽도록 수정·검증 (백업 영향이라 별도 승인)
- P3b 40_WORKING 버전 폴더(V0_1·V0_2…, R01·V01) → git 이력 통합 (사용자 승인 후)
- P4 00_GUIDE 정리 (사용자 승인 후)
- 백업 스크립트 점검 (별도 승인): SelectiveSecureBackup_v2_1은 등록부 모든 자산의 경로·SHA 일치와 옛 프로젝트 폴더(2026-11-11 삭제분 포함)를 요구 → 현재 그대로 실행하면 실패할 가능성 높음 (P3 전에도 SHA 변경 5·확인 불가 25)
- 앞으로 텍스트 변경은 커밋으로 기록 (_vN 사본 대신)
