# 자산 레지스트리 스키마 v0.1
기준 파일: asset_manifest_v0.1.json (선택 자산 7개만 포함)

## 필드 의미
- asset_id: 기능/사례를 나타내는 안정적 ID. 기존 97번 백서 및 사례 ID를 함부로 바꾸지 않는다.
- observed_original_path: 이번 감사에서 직접 파일이 존재함을 확인한 경로. 'Mac 기준 원본 보관 완료'와 다르다.
- bytes / sha256 / mtime_utc: 특정 관측 시점의 파일 메타데이터.
- observation: 기존 보고와 이번 검증 범위를 서술. 단일 통합 '완료' 상태로 사용하지 않는다.
- execution_validation: 현재 실행/운영환경 검증 여부. 이번에는 모두 NOT_TESTED_IN_THIS_AUDIT.
- write_or_execution_approval_class: 기존 자료를 수정하거나 해당 코드를 실행할 때 승인 관문. A/B/C 운영 정책 적용.
- copy_in_managed_repository: 새 원본 보관소로 복제했는지. 현재는 모든 대상 NO.
- existing_index_baseline: 기존 v1.1 DB의 기준 상태. NAS 검색 범위의 전체 판정으로 확대하지 않는다.
- unresolved: 추적해야 할 누락·검증 차이.

## 앞으로 추가할 권장 필드
source_system, source_chat_id, library_file_id, git_commit, original_asset_id,
parent_asset_ids, version, title, tags, physical_copy_locations, classification,
evidence_refs, validation_environment, validation_timestamp, reviewer, 
restore_test_id, backup_manifest_id, last_verified_sha256, approval_receipt.

## 중복 정책
SHA-256 동일 = 파일 내용 일치의 강한 근거. 동일 파일이 곧 같은 승인/운영 상태인 것은 아니다.
ZIP 내부 파일은 별도의 멤버 경로, 압축 해제 안전 검증, 개별 SHA가 있어야 한다.
같은 이름·크기만으로 원본 중복을 확정하지 않는다.

## 상태 어휘
DISCOVERED: 경로만 발견 / FILE_HASH_VERIFIED: 존재 및 SHA 확인 /
HISTORICAL_EXECUTION: 과거 성공 증거 / CURRENT_OPERATION_VERIFIED: 현 환경 실행 시험 /
RESTORE_VERIFIED: 분리 환경 복원 시험 및 대조 / NOT_ACCESSIBLE: 접근 불가 /
NOT_INDEXED: 파일이 있지만 검색 범위에서 누락.
각 상태는 자산에 중첩될 수 있으므로 단일 불리언 '검증됨'으로 단순화하지 않는다.
