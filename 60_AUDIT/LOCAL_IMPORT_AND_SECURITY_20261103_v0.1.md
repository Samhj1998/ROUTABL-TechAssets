# 120번 NAS 원본 로컬 복제 및 저장 보안 점검
기준일: 2026-11-03 KST / 원본에 쓰기·이동·삭제 없음.

## NAS 기준판의 Mac 로컬 안전 복제
원본: /Volumes/Dev_Assets/Routabl/97-1_최종내부기준판_v4.1_20261102
사본: ~/ROUTABL-TechAssets/20_ORIGINALS/NAS-Imported/ROUTABL-97-1-V4.1
복제 완료: PDF 4,907,472바이트, ZIP 3,320,156바이트, 원래 NAS 영수증.
세 파일 모두 NAS 읽기 원본과 SHA-256 일치. 사본 ZIP의 19개 항목 CRC 검사 통과.
사본 생성 영수증: 20_ORIGINALS/NAS-Imported/ROUTABL-97-1-V4.1/LOCAL_IMPORT_RECEIPT_v0.1.json
비고: Mac에서 사본을 열어 해시를 확인했으나 NAS 마운트를 실제 해제한 오프라인 복원 시험은 아님.

## 외장 SSD 점검
도구: diskutil info /Volumes/SSD2TB
파일시스템 APFS, Encrypted: No, FileVault: No (실제 검사 당시).
조치: 외장 SSD에 새로 만든 메타데이터·자산대장·감사보고서만 스냅샷 백업.
보류: 전체 백서 원본, 운영 자료, 인증 관련 파일의 무암호화 외장 SSD 복제.

## 현재 경계
암호화 이미지나 외장 SSD 자체 암호화를 임의 설정하지 않음.
기존 SSD 파일, NAS 봉인 원본, GitHub/Firebase에는 변경 없음.
본 점검으로 NAS·Google Drive 원격 전체 백업 및 재해복구가 검증되었다고 판단하지 않는다.

## 다음 승인 관문
보존 정책(암호화 방식, 보안 키의 별도 관리, 잠금 해제/복원 절차)을 설계한 뒤
외장 SSD 원본 전체 백업과 Google Drive 백업 확대를 결정한다.
v1.1 소스 수정과 다중 경로 색인 변경 역시 별도 승인 전에는 실행하지 않는다.
