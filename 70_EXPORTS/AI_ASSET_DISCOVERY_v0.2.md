# 라우터블 기술자산 검색 선행 지침 v0.2
프로젝트: 120. ROUTABL 기술자산 통합관리체계 / 기준일: 2026-11-03

## 시작 순서
1. 먼저 Mac Studio 연결 가능 여부를 확인한다. 접속 가능하면
   /Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.2.json을 읽는다.
2. 자산 ID, 태그, 관련 사례, 현재 파일 경로를 찾는다.
3. v1.1 NAS 인덱스 검색은 참고용이다. 로컬 StudioProjects는 기존 검색 범위에 포함되지 않는다.
4. 원본 현재 존재, SHA-256, 과거 시험 증거, 현행 운영 검증, 복원 상태를 분리해 보고한다.
5. 연결 실패는 자산 부재로 간주하지 않는다. Library 검색, 인계 자료, NAS 목록은 대체 경로다.
6. 검색/열람/검증은 안전 범위에서 자동화한다. 원본 수정, 운영 Firebase 쓰기, 앱 배포, 권한 변경은 사용자 승인 필수.
7. 출처별 URL/ID는 장기 식별과 향후 재검색을 돕지만 실행 권한·동기화 보증은 아니다.

## 우선 발견할 핵심 사례
- TA-CASE-20261102-01: Firebase 고객 등록 과거 성공·실패 사례.
  실제 소스: /Users/yongho/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py
  2026-11-03 직접 관측 SHA-256: de08b060d03a6b6c9f155cf89673f2285a67502cf664442b1a9bc835529a54e5
  Library 보고서: libfile_aae40558a6ec819189990681d3e6f4b2
  현재 Firebase 운영 재실행은 미검증. 중복 등록 금지. 운영 쓰기는 별도 승인.
- INTEGRATION-E04: 2026-10-19 앱/웹 통합점검 과거 보고서.
  Library HTML 식별자: libfile_1348cf4cf49c8191af70ae0162dffe99
  현행 배포 결함 판정과 분리한다. 로컬 복제/해시 대조 아직 미실시.
- ROUTABL-97-1-V4.1: NAS 봉인된 백서 내부 기준판.
  ZIP과 PDF의 NAS 영수증 SHA 대조 성공, ZIP 19개 CRC 통과.
  Library 백서 PDF 식별자: libfile_72a4f0a4043c819192d8967951f680a1
  Library 바이트 일치 검증과 독립 복원 시험은 별도 필요.

## 실수 방지
해시 일치=파일 바이트 일치일 뿐 운영 성공/승인 완료가 아니다.
'새 채팅에서 검색했다'는 사실만으로 영구 자동 연결됐다고 표현하지 않는다.
인증키/비밀번호/개인정보는 인덱스나 전달 문서에 포함하지 않는다.
현재 작업 중 코드 수정, 데이터 이동/삭제, Firebase 쓰기, NAS 봉인본 대체를 하지 않는다.
