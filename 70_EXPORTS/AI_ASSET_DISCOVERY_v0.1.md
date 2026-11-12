# 120번 기술자산 검색 선행 지침 (Chat/Work 인계용)
기준: 2026-11-03, 120. ROUTABL 기술자산 통합관리체계

라우터블·Android·Firebase·관제·백서·기술자산 관련 작업을 시작하기 전에:
1. 가능하면 Mac Studio의 ~/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.1.json을 읽는다.
2. 검색어와 자산 ID로 관련 과거 성공·실패·실행 경로를 확인한다.
3. 기존 v1.1 조회는 ~/Library/Application Support/ROUTABL-AssetSearch/routabl_assetsearch_v1_1.py의 query 기능이다.
4. 결과에 등록된 경로가 현재 존재하는지와 SHA-256 일치 여부를 따로 확인한다.
5. '검색 결과 없음'을 '기술자산 없음'이라고 단정하지 않는다. 검색 범위를 확인한다.
6. 원본 파일을 읽더라도 인증/개인정보를 외부에 출력하거나 색인하지 않는다.
7. 운영 데이터 변경, 원본 대체·삭제, 배포, 권한 변경은 사용자 명시적 승인 후에만 진행한다.
8. 재사용 후 반드시 시험 조건·실제 결과·새 증거를 별도 기록한다.

## 가장 중요한 재발견 시험
사용자 요청: 'Firebase 고객 주소록 등록해 줘'.
과거 증거: TA-CASE-20261102-01.
현재 확인 경로: ~/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py
2026-11-03 관측 SHA-256:
de08b060d03a6b6c9f155cf89673f2285a67502cf664442b1a9bc835529a54e5
주의: 기존 NAS 색인 일반 결과에서는 이 원본을 못 찾고, manual 사례만 찾는다.
경로를 확인한 것과 Firebase 현장 등록 권한·성공은 다르다.
중복 확인과 사용자 승인 없이 동일 고객을 재등록해서는 안 된다.

## 접근 실패 시
Remote Desktop Commander 연결·권한 미비, NAS 미마운트, Library 검색 한계,
색인 누락, 해시 불일치 등을 서로 다른 상태로 보고한다.
현재 연결을 확인하지 못한 경우 실행 성공이나 현재 파일 존재를 단정하지 않는다.
