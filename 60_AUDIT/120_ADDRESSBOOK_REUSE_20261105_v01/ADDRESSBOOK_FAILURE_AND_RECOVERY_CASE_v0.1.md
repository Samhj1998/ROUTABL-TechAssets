# 120 후속 — 주소록 등록 실패·복구 사례 (2026-11-05)

사례 ID: ROUTABL-ADDR-REUSE-20261105-01
보안 등급: P3 / 로컬 저장 및 암호화 백업 전용
목적: 사진 2장의 인성데이터로부터 다윤테크·세종텍스타일을 Firestore 고객 주소록에 실제 등록.
사용자 철학: 목표·대상이 명확하면 필요한 기술·수단·정보를 찾아 조직하여 완료한다. 중간 과정 성공을 전체 업무 완료로 보고하지 않는다.

## 1. 실패 응답의 정확한 상태
- 최초 새 채팅은 GPS, 지번·도로명, 중복 검사 등을 마쳤지만 Firebase 저장·동기화를 수행하지 못했다고 사용자에게 보고했다.
- Firebase 연결 기능을 새로 연결하라는 제안은 이미 존재하는 Mac Studio의 성공 실행 경로를 충분히 대조하지 못한 결과다.
- 실패했던 채팅의 전체 원본 도구 로그가 이 문서에 포함된 것은 아니다. 따라서 최초 실패의 직접 원인을 특정 권한·도구의 문제로 단정하지 않는다.

## 2. 이미 존재했던 기술자산과 연결
- 자산 ID: TA-CASE-20261102-01 (Firebase addressbook historical success script)
- 원본: /Users/yongho/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py
- v0.15 등록부 기록 SHA-256: de08b060d03a6b6c9f155cf89673f2285a67502cf664442b1a9bc835529a54e5
- 운영 DB: routivel-prod / Cloud Firestore customers. 별도의 구형 Firebase 프로젝트와 혼동 금지.
- 자산이 등록됐다는 것과 새 채팅이 자동으로 이를 찾아 실행한다는 것은 별개다.

## 3. 2026-11-05 Mac Studio 실행 이력 (한국시간)
- 11:47 기존 cloud_access.py 인증·customers 읽기 성공. 총 1,958건 중 주소·업체명 충돌 후보 확인.
- 11:53 한글 이름을 인코딩하지 않고 URL 요청 경로에 넣는 과정에서 UnicodeEncodeError 발생. Firebase 쓰기 권한이 없다는 뜻은 아니다.
- 12:02 승인된 기존 접근 경로를 사용해 Firestore commit 방식으로 두 업체를 신규 저장하고 서버에서 재조회. 출력상 두 업체 모두 savedVerified=true.
- 12:02 customerDirectoryChanges 변경 저널 대조. 출력상 두 업체 모두 incrementalSyncVerified=true.
- 전화번호·토큰·고객 인증정보 원문은 개인정보 최소화 원칙에 따라 본 감사 문서에서 제외.
- 근거는 Desktop Commander의 최근 실행 도구 이력 출력. 해당 도구 이력 전체를 영구·불변 원본으로 봉인한 것은 아니므로 증거 강도를 구분한다.

## 4. 결론과 유의점
- 최종 결과: 다윤테크·세종텍스타일 2건 Firestore 저장/재조회 및 변경 저널 확인 성공.
- 모바일 앱 자체에서 실제 목록 반영까지 눈으로 확인한 실기기 시험 기록은 별도로 없다. 저널 성공과 앱 표시 성공을 혼동하지 않는다.
- 최초 실패는 목표보다 개별 도구의 한계를 우선시한 작업 중단 문제이자 기술자산 발견·재사용 체계의 미완성을 드러낸다.
- 일부 도구/요청 방식이 실패하더라도 승인된 다른 경로를 검토해야 한다. 보안 차단이나 권한을 무단 우회하지 않는다.
- 기존 주소록·Firebase·개발 코드는 이번 등록부 기록 작업에서 변경하지 않는다.

## 5. 후속 개선 항목
1. ASSET-SEARCH-03: 새 채팅에서도 검증된 성공 스크립트 및 런북을 첫 단계에서 자동 검색하도록 연결.
2. 주소 등록 전 중복 검사, 신규 create-only 조건, 저장 재조회, 고객변경 저널 비교를 필수 완료 기준으로 고정.
3. 모든 실행의 개인정보 제외 영수증(작업 회차·문서 ID·서버 updateTime·검증 결과) 보존 절차 설계.
4. 기사용/고객용 앱에서 동기화가 실제 표시되는 실기기 점검은 별도 수행.
5. 최초 실패 채팅의 상세 실행 로그를 확보하면 직접 장애 원인 분석을 추가하되 기존 기록을 덮어쓰지 않는다.

연계 파일: ADDRESSBOOK_REGISTRATION_RUNBOOK_v0.1.md, ADDRESSBOOK_EVIDENCE_AND_ACCEPTANCE_v0.1.json
