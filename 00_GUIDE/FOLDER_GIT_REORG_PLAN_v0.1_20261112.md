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

## 다음 행동
- 등록부 갱신 방법(앞으로): asset_manifest.json 수정 → 커밋 → 이름표 registry-v0.N. v0.N 사본은 만들지 않음
- 남은 호환 사본 v0.32 제거 조건: 백업 스크립트가 asset_manifest.json을 읽도록 수정·검증 (백업 영향이라 별도 승인)
- P3 40_WORKING 정리 (사용자 승인 후)
- 앞으로 텍스트 변경은 커밋으로 기록 (_vN 사본 대신)
