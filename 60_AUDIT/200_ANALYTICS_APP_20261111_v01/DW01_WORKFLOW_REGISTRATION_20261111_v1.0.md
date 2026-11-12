# DW-01 두 AI 분업 개발 방식 등록 기록 v1.0

- 작성: 2026-11-11 KST, Claude 세션 (사용자 요청 "이 방식 기술자산에 업데이트해줘")
- 등록부: `asset_manifest_v0.29.json` (v0.28 내용 무변경 + 3건 추가 + `dual_ai_workflow_v029`)
- 검색 색인: `asset_120_lookup_v0.15.sqlite` (v0.14 복사 + 3행, 178행, integrity_check ok)
- 원칙 문서: `00_GUIDE/ROUTABL_DUAL_AI_BUILD_WORKFLOW_DW01_v1.0_20261111.md` (sha256 ad688f9d…f234222)

## 추가 자산

| asset_id | 검증 상태 |
|---|---|
| ASSET-120-GOVERNANCE-DW01-DUAL-AI-BUILD-WORKFLOW-20261111 | 원칙 문서 등록, 첫 적용 b960472 |
| ANALYTICS-APP-01-SHARED-HASH-GUARD | Mac Gradle 빌드 통과, 부정 시험 감지, origin/main 반영 |
| ANALYTICS-APP-01-HANDOFF-20261111 | 문서 커밋 b6d8914, 푸시 |

## 해시 (등록 시점)

- v0.28 등록부 21460c06…1e6cae, v0.14 색인 baa40be7…518eb45 → 작업 전후 동일 (cmp 확인)
- v0.29 등록부 78f13278…847d512f, v0.15 색인 3e409623…a0ec29

## 작업 방식

- v0.14 사고(연결 폴더 위 sqlite 직접 생성 실패)를 피해, 로컬 작업 폴더에서 만든 뒤 복사(cp -n, 덮어쓰기 없음)

## 하지 않은 것

- 기존 v0.28·v0.14, 97-1 봉인본, NAS 백업, `~/Library` 자산 검색 서비스 DB, Firebase, 앱 코드: 변경 없음
- 자산 검색 앱(v1.5)에서는 색인을 다시 만들기 전까지 새 항목이 보이지 않음
- 기존 `ANALYTICS-APP-01-READONLY-BUILD-GUARD`(v0.28)의 해시는 수정 전 파일 기준으로 그대로 둠. 현재 해시는 v0.29 `note_existing_entry`에 기록
