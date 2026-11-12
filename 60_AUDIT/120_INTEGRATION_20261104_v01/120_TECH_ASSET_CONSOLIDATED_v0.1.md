# 120. 라우터블 기술자산 통합관리체계 — 증거 계보·검색·보안 백업 통합 갱신 v0.1
작성: 2026-11-04T09:29:23+09:00 KST · 등록부 후속 판본 v0.15
**성격:** 확인 가능한 실환경 원본 및 로그에 근거한 현행 통합 기록. 120번 채팅 전체 원문 아님.
**상태:** 운영 승인 및 백그라운드 단발 전체 검증 PASS / 최초 정기 04:30 예약 발동은 아직 미검증.

## 1. 기술자산체계 범위
- ASSET-SEARCH-01: Mac/NAS/개발 소스 검색과 원본 경로·태그·SHA 색인.
- ASSET-SEARCH-02: Mac + 외장 SSD + NAS 보존 및 복구 가능성 점검.
- ASSET-SEARCH-03: 새 채팅/앱 개발에서 기술자산 사전 조회·재사용 절차(자동 적용은 미완).
- ASSET-ARCHIVE-01: ChatGPT Library/대화 원본, Mac 및 NAS 증거보관 계보(원문 전량 확보 미완).
- ASSET-SECURITY-01: 사용자 승인, 접근 권한, 읽기/쓰기 경계, 오류안전/감사 로그.

## 2. 등록부·검색
- 검증된 직전 자산대장: asset_manifest_v0.14.json (81/81 SHA-256 일치; 원본 변경 없음).
- 별도 검색 v1.5 인덱스: SQLite 총 5,519개 docs 검색 가능(기존 사용자 GUI 새로고침 시험 기록 존재).
- 검색 v1.5는 현재 ROUTABL-TechAssets/60_AUDIT 및 30_REGISTRY를 색인하지 않음(120_*.md 0건). 기존 앱 v1.5를 이번 등록으로 임의 변경하지 않음.
- 이번 갱신은 v0.15 등록부와 별도 메타데이터 전용 보조 SQLite를 만든다. UI 통합은 별도 변경 승인 및 회귀 시험 항목이다.

## 3. 배경 권한 문제와 해결
- 과거 v0.2 에이전트 네트워크 볼륨 최초 접근 시 TCC 접근 요청·응답 대기 발생.
- v0.4.2 접근 시험 동의 scope=TCC_METADATA_READ_ONLY, 실제 백업과 별개.
- NAS 네트워크/제거 가능 볼륨 macOS 권한 토글 허용: 사용자가 시스템 설정 화면으로 확인.
- 초기 네트워크 진단 결과 PROBE_TIMEOUT_NO_RETRY (20.3초); 동일 고정 v0.4.2 승인 권한으로 재실행 시 PASS_PERMISSION_METADATA_ONLY (0.1초).
- macOS 보안 권한 우회·자동 클릭·TCC.db 수정 금지 유지.
- 운영 승인 파일 생성: 사용자 별도 명시 지시 이후, 소유 UID 501·0600·범위 MAC_SSD_AES256_TO_NAS_CAS_ONLY·04:30·Drive 업로드=false·pruning=false.
- 실제 등록 에이전트: com.routabl.assetbackup.native.v042 (KeepAlive=false, RunAtLoad=false, daily 04:30).
- 사용한 앱: 라우터블 백업 권한·안전관리 v0.4.2; 서명/무결성 확인 및 실제 launchctl 단발 성공.
- 예전 NAS/Drive 등 백업 예약은 disabled 유지.

## 4. 첫 무인 경로 수동 기동 실증
- 실행: 2026-11-04T08:46:24+09:00 완료 (04:30 자동 시각이 아닌 별도 kickstart).
- 네이티브 에이전트: BACKUP_VERIFIED_RECEIPT_CURRENT; 종료 코드 0.
- 감독 프로그램: SUCCESS_VERIFIED; actual_backup_success=true.
- SSD 스냅샷: ASSET_V21_20261104_084130_KST_34561.
- 저장 자산 파일: 3,328개; 원본 총 519,889,613바이트.
- SSD: SHA-256 전수 비교 성공, 독립 복원 표본 15개, AES 이미지 마운트 해제.
- NAS 결과: SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS; 새 암호문 573,710,336바이트,
  신규 암호화 구성요소 70개, 재사용 325개,
  총 395개.
- NAS CAS 매니페스트: CAS_ASSET_V21_20261104_084130_KST_34561.json; completed=true, anchor 보존 필수.
- 영수증 계보: supervisor/local/NAS snapshot, manifest SHA, receipt SHA 모두 일치 확인.
- 기존 백업 덮어쓰기·삭제·pruning 및 Drive 원격 전송 없음.

## 5. 복원 범위의 엄격한 구분
- 새 3328개 스냅샷: SSD 내부 해시/표본 복원과 NAS CAS 전체 구성파일 검증 완료.
- 구버전 별도 QA 영수증: PASS_CAS_CIPHERTEXT_FULL_RESTORE (기준 회차 상이). 최신 스냅샷 전체 복호화/내부파일 전수 복원 검증으로 대체하여 표기하지 않음.
- NAS의 기준(full anchor) 암호화 복제본을 변경·삭제하면 증분 체인이 무효화될 수 있으므로 무기한 보존.

## 6. 변경 경계 및 운영 조건
- 기술자산 감사·등록 메타데이터만 신규 작성. 기존 Android 앱, Firebase/Firestore, GitHub, 원본 프로젝트 소스 수정 0건.
- macOS 사용자 세션(UID 501), Mac Studio 전원 유지 및 SSD/NAS 연결 필요.
- 전원 상태 sleep=0 확인; Mac 재시동 후 NAS SMB 재연결, Keychain 및 실제 매일 자동 발동은 추가 운영 검증 필요.
- Google Drive 직접 자동 업로드는 사용자가 정한 범위 밖. Synology Cloud Sync 주간 외부 보관은 본 기록에서 실증하지 않음.
- 보안: 인증키·비밀번호·Firebase Admin JSON 등의 원본은 등록부/반출 파일에 넣지 않음.

## 7. 증거 인용·재사용
- 목록·파일별 SHA: EVIDENCE_CATALOG_v0.1.json.
- 변경 가능한 실행 로그 원본 → 캡처 시점 SHA 일치하는 IMMUTABLE_RECEIPTS/ 사본 → v0.15 등록부 연결.
- 전체 120번 대화 원문·시각·첨부는 미확보로 분명히 표시.
- 차기 공식 04:30 실행(2026-11-05)과 연속 가동/복원 검증 완료 전에는 운영 안정화 최종 확정 금지.
