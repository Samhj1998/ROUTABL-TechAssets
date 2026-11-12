# 120번 NAS 정기 백업 2026-11-08 읽기 전용 원인 분석

상태: 진단 결과 후보 / 운영 변경 없음 / 실제 04:30 오류의 최종 원인 미확정
장치: MacStudioui-MacStudio.local / c377300b-a710-43a6-8169-f17e87175403
근거: 2026-11-08 07:30 예약 검증 보고 및 당일 Mac Studio 로컬 영수증·실행 코드·현재 선택기 진단.
비밀명 파일명·경로·전화번호·고객 원문은 보고·외부 공유에서 제외.

## 확정 관찰

1. last_native_launchagent_v04.json: at 2026-11-07T19:30:06Z = 11/08 04:30:06 KST, phase=postbackup, childExitCode=0, state=BACKUP_VERIFIED_RECEIPT_CURRENT. 이는 실제 신규 백업 영수증을 대조한 결과와 일치하지 않는다.
2. last_native_backup_supervisor_v01.json: 11/08 04:30:24 KST, state=FAILED_ONE_ATTEMPT_NO_RETRY, returncode=2, actual_backup_success=false.
3. last_native_backup_supervisor_v02.json: 11/08 04:30:06 KST, state=SUCCESS_VERIFIED, actual_backup_success=true라고 표기했으나 local_snapshot=ASSET_V21_20261106_043146_KST_59950, backed_up_files=3373. 오늘 신규 백업과 다른 날짜.
4. last_selective_v21_result.json: 11/06 04:31:54 KST 성공, manifest_name=asset_manifest_v0.19.json, snapshot=ASSET_V21_20261106_043146_KST_59950.
5. last_manual_mac_nas_cas_v01.json: 11/06 04:41:22 KST 성공, 해당 v0.19, 로컬 snapshot과 NAS CAS 연결.
6. 최신 공식 자산대장 30_REGISTRY/asset_manifest_v0.27.json SHA256 afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244. 11/08 신규 v0.27 로컬·NAS 성공 증거 없음.
7. /bin/launchctl list 읽기 결과: com.routabl.assetbackup.native.v042 (마지막 종료코드 0), com.routabl.assetbackup.native.v02 (마지막 종료코드 7). 둘이 등록돼 있지만 같은 순간 실제 경합했는지 직접 입증하지 않음.
8. /Users/yongho/ROUTABL-TechAssets/00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_2.py 의 postflight 성공 판정은 LAST/LOCAL 영수증끼리 snapshot, receipt, manifest 일치 및 MOUNT 부재를 확인하되, 현재 날짜, 최신 공식 대장, 최신 선택 목록 및 이번 실행에서 새 작업을 실제로 했는지는 확인하지 않음. 따라서 과거 성공 영수증의 오판 가능성이 코드상 확인됨.
9. /Users/yongho/ROUTABL-TechAssets/00_GUIDE/ROUTABL_MacToNasOneShot_v0_1.py 의 예외 처리는 원인 메시지 없이 FAILED_SAFE, failure_type만 stderr에 출력하고 코드 2로 종료. v02 감독자는 자식 stdout/stderr를 DEVNULL로 버림. 따라서 04:30 당시 OneShot 내부 실패 지점을 현 영수증으로 확정할 수 없음.
10. 현재 선택기 /Users/yongho/ROUTABL-TechAssets/00_GUIDE/ROUTABL_SelectiveSecureBackup_v2_1.py 의 inventory()를 읽기 전용으로 독립 호출: latest_registry=asset_manifest_v0.27.json, RuntimeError=NOT_ALL_40_VERIFIED_ASSETS_CLEARED_SECURITY_CHECK. 현재 공식 등록자산 162개 중 안전검사 통과 160, 불합격 2. 사유 분류 secret_named_path 1, direct_customer_identifier 1. 통과한 160개의 바이트·크기 SHA 대장 불일치 0. 이름의 40은 오래된 상수 문자열이며 실제 등록건수 162와 무관. 두 제외 대상의 원문과 경로는 출력하지 않음.

## 판단

- 당일 04:30 신규 백업 완료: FAIL/NOT_VERIFIED (성공 증거 부재, 실패 감독 영수증).
- 등록자산 전체를 백업 선택기에 통과시키지 못하는 현재 차단 조건: READ_ONLY_REPRODUCED.
- 과거 영수증을 현재 성공으로 선언하는 감독자 설계 결함: SOURCE_CONFIRMED.
- 실제 04:30 OneShot의 정확한 단일 실패 지점: NOT_VERIFIED. 당시 코드 2, 원인 세부로그 보존 부재. 현 시점 2건 차단이 11/07, 11/08 실패의 강력한 설명 후보지만 과거 프로세스 내부 단계까지 실증된 것은 아님.
- 이중 launchd 등록과 실제 자식 충돌의 인과관계: NOT_VERIFIED.

## 원칙 및 승인 경계

- 민감 자료 2건을 보안검사에서 무단 허용하거나 등록부 원본을 삭제·수정하여 PASS로 만들지 말 것.
- 선순환 최소 완성판 MVL-01 격리 개발은 계속할 수 있으나, 운영 기술자산 최신 백업 보호 수준은 11/06 v0.19 증거까지만 확인됨을 별도 위험으로 관리.
- 개선 설계 방향: 등록자산 관리와 백업 대상 적격성의 분리, 민감 자산은 비밀 보호/비식별 처리 또는 제외 증빙, 나머지 안전한 자산은 하나의 제외 사유 때문에 전체 보호되지 않는 문제의 단계적 개선. 위반 데이터 원문/토큰/개인정보는 계속 보호.
- 운영 수정, 재실행, 승인파일 및 예약/권한/매체 변경, 공식 Step5C는 이번 조사 범위 밖이며 별도 승인.
- 후속 격리 Work 과제: v0.27 안전검사 탈락 카테고리 2건 재현, 올바른 백업 적격성 정책 설계, 오늘-최신 계보 기반 성공 판정 및 구형 라벨 충돌·종료 코드 원인 관측 개선, 합성시험, 실제 운영 변경 없는 패치 후보·증거. 목표는 새로운 Gate 무한 추가가 아니라 최소 기능 회복.
