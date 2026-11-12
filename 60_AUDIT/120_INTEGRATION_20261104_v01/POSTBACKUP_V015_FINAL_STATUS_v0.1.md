# 120번 통합 자산대장 v0.15 — 백업 후 최종 검증 기록
2026-11-04 09:42 KST 관측 (Mac Studio 읽기 전용 검증)

## 확인된 결과
- 기존 v0.14 자산 81건은 SHA-256 81/81 일치, 기존 파일 원본 유지.
- v0.15 신규 자산 18건 추가, 등록 총 99건; 99/99 원본 SHA-256 일치.
- v0.15 등록부 SHA-256: cc84d033c02ee215ce8a1cf0f7635f3c541295a34bfa0f1f1da6175121fdeda2.
- 검색 보조 SQLite 99건, SQLite integrity_check=ok. 기존 v1.5 검색 DB는 변경하지 않음.
- 암호화 SSD 스냅샷: ASSET_V21_20261104_093408_KST_35618, 3,344개 파일.
- SSD SHA-256 검증 PASS, 독립 복원 표본 15개 PASS, AES 이미지 자동 마운트 해제 PASS.
- NAS 영수증: SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS, 완료 2026-11-04 09:41:24 KST.
- NAS CAS 구성요소 458개, 이번 회차 신규 암호문 585,756,672바이트, 기존 암호문 387개 재사용.
- NAS 매니페스트 CAS_ASSET_V21_20261104_093408_KST_35618.json, completed=true 및 스냅샷 계보 일치.
- Supervisor SUCCESS_VERIFIED, 네이티브 에이전트 BACKUP_VERIFIED_RECEIPT_CURRENT, 최종 종료 코드 0.
- 최종 점검 항목 15/15 PASS.
- Google Drive 자동 업로드 및 NAS 기준본 삭제·정리 없음.

## 증거와 한계
- 실제 실행 영수증(원본은 추후 갱신 가능): ~/Library/Logs/ROUTABL-AssetBackup/last_native_launchagent_v04.json, last_native_backup_supervisor_v02.json, last_selective_v21_result.json, last_manual_mac_nas_cas_v01.json.
- NAS에 저장된 CAS 매니페스트는 본 회차 암호문 구성의 독립적인 계보 증거이다.
- 본 문서는 09:34 시작된 SSD 백업 **이후** 기록했으므로 그 회차의 스냅샷에 포함되어 있지 않다. 다음 정기 백업에서 보존을 확인해야 한다.
- 2026-11-05 04:30 정기 자동 발동은 아직 검증 전. 별도 7일 읽기 전용 점검 예약함.
- 120번 전체 채팅 원본 및 최신 회차 NAS에서 내부 3,344개 전수 복호화 시험은 미확보·미실행. 관련 공동 해결 목록은 OPEN_ISSUES_FOR_OWNER_v0.1.md.
- Android·Firestore·GitHub 운영 자료는 변경하지 않았다.
